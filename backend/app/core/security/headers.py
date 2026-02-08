"""
Security headers middleware.

セキュリティヘッダーミドルウェア。
OWASP推奨のセキュリティヘッダーをレスポンスに追加。
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


# デフォルトセキュリティヘッダー
DEFAULT_SECURITY_HEADERS: Dict[str, str] = {
    # XSS保護
    "X-XSS-Protection": "1; mode=block",

    # コンテンツタイプのスニッフィングを防止
    "X-Content-Type-Options": "nosniff",

    # クリックジャッキング防止
    "X-Frame-Options": "DENY",

    # Referrer情報の制限
    "Referrer-Policy": "strict-origin-when-cross-origin",

    # キャッシュ制御（API向け）
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",

    # 権限ポリシー（不要な機能を無効化）
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# 本番環境用の追加ヘッダー
PRODUCTION_HEADERS: Dict[str, str] = {
    # HTTPS強制
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",

    # CSP（Content Security Policy）
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
}


class SecurityHeadersMiddleware:
    """
    セキュリティヘッダーミドルウェア。

    全レスポンスにセキュリティヘッダーを追加。
    本番環境ではHSTSとCSPも追加。
    """

    def __init__(self, app, production: bool = False):
        """
        ミドルウェアを初期化。

        Args:
            app: ASGIアプリケーション
            production: 本番モードかどうか
        """
        self.app = app
        self.production = production
        self.headers = self._build_headers()

    def _build_headers(self) -> list:
        """適用するヘッダーのリストを構築"""
        headers_dict = DEFAULT_SECURITY_HEADERS.copy()

        if self.production:
            headers_dict.update(PRODUCTION_HEADERS)
            logger.info("Security headers configured for production mode")
        else:
            logger.info("Security headers configured for development mode (no HSTS/CSP)")

        # バイト形式に変換
        return [(k.lower().encode(), v.encode()) for k, v in headers_dict.items()]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # 既存のヘッダーを取得
                existing_headers = list(message.get("headers", []))

                # セキュリティヘッダーを追加
                existing_header_names = {h[0] for h in existing_headers}
                for header_name, header_value in self.headers:
                    if header_name not in existing_header_names:
                        existing_headers.append((header_name, header_value))

                message["headers"] = existing_headers

            await send(message)

        await self.app(scope, receive, send_wrapper)


def get_security_headers(production: bool = False) -> Dict[str, str]:
    """
    セキュリティヘッダーの辞書を取得。

    Args:
        production: 本番モードかどうか

    Returns:
        Dict[str, str]: ヘッダー辞書
    """
    headers = DEFAULT_SECURITY_HEADERS.copy()
    if production:
        headers.update(PRODUCTION_HEADERS)
    return headers
