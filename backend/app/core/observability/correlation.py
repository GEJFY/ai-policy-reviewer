"""
Correlation ID management for distributed tracing.

分散トレーシング用の相関ID管理。
サービス間でリクエストを追跡するためのコンテキスト変数を提供。
"""

from contextvars import ContextVar
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)

# コンテキスト変数（スレッドセーフ、async対応）
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
session_id: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
client_ip: ContextVar[Optional[str]] = ContextVar("client_ip", default=None)


class CorrelationContext:
    """
    相関コンテキスト管理クラス。

    リクエスト全体で一貫した追跡情報を提供する。
    ログ、メトリクス、監査ログで使用。
    """

    @staticmethod
    def generate_id() -> str:
        """新しい相関IDを生成。"""
        return str(uuid.uuid4())

    @staticmethod
    def get_correlation_id() -> str:
        """
        現在の相関IDを取得。

        設定されていない場合は新規生成して設定。
        """
        cid = correlation_id.get()
        if not cid:
            cid = CorrelationContext.generate_id()
            correlation_id.set(cid)
        return cid

    @staticmethod
    def get_short_id() -> str:
        """短縮相関ID（8文字）を取得。ログ出力用。"""
        return CorrelationContext.get_correlation_id()[:8]

    @staticmethod
    def set_correlation_id(cid: str) -> None:
        """相関IDを設定。"""
        correlation_id.set(cid)

    @staticmethod
    def get_user_id() -> Optional[str]:
        """現在のユーザーIDを取得。"""
        return user_id.get()

    @staticmethod
    def set_user_id(uid: Optional[str]) -> None:
        """ユーザーIDを設定。"""
        user_id.set(uid)

    @staticmethod
    def get_session_id() -> Optional[str]:
        """現在のセッションIDを取得。"""
        return session_id.get()

    @staticmethod
    def set_session_id(sid: Optional[str]) -> None:
        """セッションIDを設定。"""
        session_id.set(sid)

    @staticmethod
    def get_client_ip() -> Optional[str]:
        """クライアントIPを取得。"""
        return client_ip.get()

    @staticmethod
    def set_client_ip(ip: Optional[str]) -> None:
        """クライアントIPを設定。"""
        client_ip.set(ip)

    @staticmethod
    def set_from_request(
        request_id: str,
        user: Optional[str] = None,
        session: Optional[str] = None,
        ip: Optional[str] = None,
    ) -> None:
        """
        リクエストから相関コンテキストを設定。

        Args:
            request_id: リクエストID（相関ID）
            user: ユーザーID
            session: セッションID
            ip: クライアントIP
        """
        correlation_id.set(request_id)
        if user:
            user_id.set(user)
        if session:
            session_id.set(session)
        if ip:
            client_ip.set(ip)

    @staticmethod
    def clear() -> None:
        """コンテキストをクリア。"""
        correlation_id.set("")
        user_id.set(None)
        session_id.set(None)
        client_ip.set(None)

    @staticmethod
    def get_context_dict() -> dict:
        """
        現在のコンテキストを辞書形式で取得。

        ログ出力やメトリクスラベルに使用。
        """
        return {
            "correlation_id": CorrelationContext.get_correlation_id(),
            "user_id": user_id.get(),
            "session_id": session_id.get(),
            "client_ip": client_ip.get(),
        }


class CorrelationLogFilter(logging.Filter):
    """
    ログに相関IDを自動付与するフィルター。

    Usage:
        handler.addFilter(CorrelationLogFilter())
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """ログレコードに相関情報を追加。"""
        record.correlation_id = CorrelationContext.get_short_id()
        record.user_id = user_id.get() or "-"
        record.client_ip = client_ip.get() or "-"
        return True


class CorrelationMiddleware:
    """
    FastAPI用の相関IDミドルウェア。

    各リクエストに対して相関IDを設定し、レスポンスヘッダーに追加。
    X-Request-IDヘッダーがあればそれを使用、なければ新規生成。
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # ヘッダーから相関IDを取得または生成
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode("utf-8")
        if not request_id:
            request_id = headers.get(b"x-correlation-id", b"").decode("utf-8")
        if not request_id:
            request_id = CorrelationContext.generate_id()

        # クライアントIPを取得
        client = scope.get("client")
        client_ip_value = client[0] if client else None

        # X-Forwarded-Forヘッダーをチェック（プロキシ経由の場合）
        forwarded_for = headers.get(b"x-forwarded-for", b"").decode("utf-8")
        if forwarded_for:
            # 最初のIPがクライアントIP
            client_ip_value = forwarded_for.split(",")[0].strip()

        # コンテキストを設定
        CorrelationContext.set_from_request(
            request_id=request_id,
            ip=client_ip_value,
        )

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # レスポンスヘッダーに相関IDを追加
                headers = list(message.get("headers", []))
                headers.append((b"x-correlation-id", request_id.encode("utf-8")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # リクエスト終了時にコンテキストをクリア
            CorrelationContext.clear()
