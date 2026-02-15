"""
Rate limiting for API protection.

API保護のためのレート制限。
IPベースおよびユーザーベースのレート制限を提供。
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from fastapi import Request

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """レート制限設定"""

    requests: int  # 許可するリクエスト数
    window_seconds: int  # ウィンドウ期間（秒）
    burst: int = 0  # バースト許容数（0の場合requestsと同じ）

    def __post_init__(self):
        if self.burst == 0:
            self.burst = self.requests


@dataclass
class RateLimitState:
    """レート制限状態"""

    tokens: float  # 現在のトークン数
    last_update: float  # 最終更新時刻
    request_count: int = 0  # 総リクエスト数


# エンドポイント別のレート制限設定
RATE_LIMITS: Dict[str, RateLimitConfig] = {
    # 認証関連（厳しめ）
    "/api/v1/auth/login": RateLimitConfig(requests=5, window_seconds=60),
    "/api/v1/auth/register": RateLimitConfig(requests=3, window_seconds=60),
    "/api/v1/auth/password-reset": RateLimitConfig(requests=3, window_seconds=60),
    # ドキュメント操作
    "/api/v1/documents/upload": RateLimitConfig(requests=10, window_seconds=60),
    "/api/v1/documents": RateLimitConfig(requests=30, window_seconds=60),
    # レビュー操作（LLM呼び出しを含むため）
    "/api/v1/reviews": RateLimitConfig(requests=20, window_seconds=60),
    "/api/v1/reviews/{id}/start": RateLimitConfig(requests=5, window_seconds=60),
    # マスタデータ
    "/api/v1/terms": RateLimitConfig(requests=60, window_seconds=60),
    "/api/v1/check-items": RateLimitConfig(requests=60, window_seconds=60),
    "/api/v1/writing-rules": RateLimitConfig(requests=60, window_seconds=60),
    # デフォルト
    "default": RateLimitConfig(requests=100, window_seconds=60),
}


class RateLimiter:
    """
    トークンバケット方式のレート制限。

    IPアドレスごとにリクエスト数を制限する。
    ユーザー認証がある場合はユーザーIDでも制限可能。
    """

    def __init__(self):
        self._states: Dict[str, RateLimitState] = defaultdict(
            lambda: RateLimitState(tokens=100.0, last_update=time.time())
        )
        self._lock = asyncio.Lock()
        self._cleanup_interval = 300  # 5分ごとにクリーンアップ
        self._last_cleanup = time.time()

    def _get_config(self, path: str) -> RateLimitConfig:
        """パスに対応するレート制限設定を取得"""
        # 完全一致
        if path in RATE_LIMITS:
            return RATE_LIMITS[path]

        # プレフィックスマッチ（パラメータなしのパス）
        for pattern, config in RATE_LIMITS.items():
            if pattern == "default":
                continue
            # {id} などのパラメータを含むパターンのチェック
            if "{" in pattern:
                base_pattern = pattern.split("{")[0]
                if path.startswith(base_pattern):
                    return config

        return RATE_LIMITS["default"]

    def _get_key(self, request: Request, user_id: Optional[str] = None) -> str:
        """レート制限のキーを生成"""
        # クライアントIP取得
        client_ip = request.client.host if request.client else "unknown"

        # X-Forwarded-For対応
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        # ユーザーIDがあればそれも含める
        if user_id:
            return f"{client_ip}:{user_id}:{request.url.path}"

        return f"{client_ip}:{request.url.path}"

    async def _refill_tokens(
        self, state: RateLimitState, config: RateLimitConfig
    ) -> None:
        """トークンを補充"""
        now = time.time()
        elapsed = now - state.last_update

        # トークン補充レート（1秒あたり）
        refill_rate = config.requests / config.window_seconds
        tokens_to_add = elapsed * refill_rate

        state.tokens = min(config.burst, state.tokens + tokens_to_add)
        state.last_update = now

    async def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None,
    ) -> Tuple[bool, Dict]:
        """
        レート制限をチェック。

        Args:
            request: FastAPIリクエスト
            user_id: ユーザーID（認証済みの場合）

        Returns:
            Tuple[bool, Dict]: (許可されたか, ヘッダー情報)
        """
        async with self._lock:
            # クリーンアップ
            await self._cleanup_if_needed()

            key = self._get_key(request, user_id)
            config = self._get_config(request.url.path)

            # 新規キーの場合は初期化
            if key not in self._states:
                self._states[key] = RateLimitState(
                    tokens=float(config.burst),
                    last_update=time.time(),
                )

            state = self._states[key]

            # トークン補充
            await self._refill_tokens(state, config)

            # レート制限ヘッダー情報
            headers = {
                "X-RateLimit-Limit": str(config.requests),
                "X-RateLimit-Remaining": str(max(0, int(state.tokens) - 1)),
                "X-RateLimit-Reset": str(
                    int(state.last_update + config.window_seconds)
                ),
            }

            # トークンチェック
            if state.tokens < 1:
                retry_after = int(
                    config.window_seconds - (time.time() - state.last_update)
                )
                headers["Retry-After"] = str(max(1, retry_after))
                logger.warning(
                    f"Rate limit exceeded | key={key} | path={request.url.path} | "
                    f"remaining={state.tokens:.2f}"
                )
                return False, headers

            # トークン消費
            state.tokens -= 1
            state.request_count += 1

            return True, headers

    async def _cleanup_if_needed(self) -> None:
        """古い状態をクリーンアップ"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        # 期限切れの状態を削除
        expired_keys = [
            key
            for key, state in self._states.items()
            if now - state.last_update > 3600  # 1時間経過
        ]

        for key in expired_keys:
            del self._states[key]

        if expired_keys:
            logger.debug(f"Rate limiter cleanup | removed={len(expired_keys)}")

        self._last_cleanup = now

    def get_stats(self) -> Dict:
        """統計情報を取得"""
        return {
            "total_keys": len(self._states),
            "configs": {
                k: {"requests": v.requests, "window": v.window_seconds}
                for k, v in RATE_LIMITS.items()
            },
        }


# シングルトンインスタンス
rate_limiter = RateLimiter()


class RateLimitMiddleware:
    """
    FastAPI用レート制限ミドルウェア。

    全リクエストにレート制限を適用。
    制限超過時は429 Too Many Requestsを返す。
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # デバッグモードではレート制限を無効化
        from app.config import settings

        if settings.debug:
            await self.app(scope, receive, send)
            return

        # 静的ファイルやヘルスチェックは除外
        path = scope["path"]
        if path in [
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
            "/docs",
            "/openapi.json",
        ]:
            await self.app(scope, receive, send)
            return

        # モックリクエストオブジェクト作成
        from starlette.requests import Request as StarletteRequest

        request = StarletteRequest(scope, receive)

        # レート制限チェック
        allowed, headers = await rate_limiter.check_rate_limit(request)

        if not allowed:
            # 429レスポンス
            response_headers = [
                (b"content-type", b"application/json"),
                *[(k.lower().encode(), str(v).encode()) for k, v in headers.items()],
            ]

            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": response_headers,
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"detail": "Too many requests. Please try again later."}',
                }
            )
            return

        # レート制限ヘッダーを追加してレスポンス
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                existing_headers = list(message.get("headers", []))
                for key, value in headers.items():
                    existing_headers.append((key.lower().encode(), str(value).encode()))
                message["headers"] = existing_headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
