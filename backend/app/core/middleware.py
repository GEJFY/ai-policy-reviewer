"""
FastAPIミドルウェア
リクエスト/レスポンスのログ記録とエラーハンドリングを提供
"""

import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.logging_config import get_logger
from app.core.exceptions import (
    PolicyReviewerException,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError,
    ExternalServiceError,
    ServiceUnavailableError,
    RateLimitExceededError,
)

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTPリクエスト/レスポンスをログに記録するミドルウェア

    記録内容:
    - リクエストID（トレーサビリティ用）
    - メソッド、パス
    - 処理時間
    - ステータスコード
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # リクエストIDを生成
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # リクエスト開始をログ
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        client_ip = request.client.host if request.client else "unknown"

        logger.info(
            f"Request start | request_id={request_id} | method={method} | "
            f"path={path} | query={query} | client_ip={client_ip}"
        )

        # 処理時間計測
        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # レスポンスログ
            logger.info(
                f"Request end | request_id={request_id} | method={method} | "
                f"path={path} | status={response.status_code} | "
                f"duration_ms={duration_ms:.2f}"
            )

            # レスポンスヘッダーにリクエストIDを追加
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request error | request_id={request_id} | method={method} | "
                f"path={path} | duration_ms={duration_ms:.2f} | "
                f"error={str(e)}"
            )
            raise


def add_exception_handlers(app: FastAPI) -> None:
    """
    グローバル例外ハンドラーを追加

    Args:
        app: FastAPIアプリケーション
    """

    # ============================================================
    # カスタム例外ハンドラー
    # ============================================================

    @app.exception_handler(PolicyReviewerException)
    async def policy_reviewer_exception_handler(request: Request, exc: PolicyReviewerException):
        """アプリケーション固有の例外ハンドラー"""
        request_id = getattr(request.state, "request_id", "unknown")

        # エラーコードに基づいてHTTPステータスコードを決定
        status_code = _get_status_code_for_exception(exc)

        logger.warning(
            f"{exc.error_code} | request_id={request_id} | "
            f"message={exc.message} | details={exc.details}"
        )

        return JSONResponse(
            status_code=status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(f"AuthenticationError | request_id={request_id} | error={exc.message}")
        return JSONResponse(
            status_code=401,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
                "request_id": request_id,
            },
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request: Request, exc: AuthorizationError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(f"AuthorizationError | request_id={request_id} | error={exc.message}")
        return JSONResponse(
            status_code=403,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
                "request_id": request_id,
            },
        )

    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(f"ResourceNotFoundError | request_id={request_id} | error={exc.message}")
        return JSONResponse(
            status_code=404,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(f"ValidationError | request_id={request_id} | error={exc.message}")
        return JSONResponse(
            status_code=400,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(f"ServiceUnavailableError | request_id={request_id} | error={exc.message}")
        return JSONResponse(
            status_code=503,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(f"RateLimitExceededError | request_id={request_id} | error={exc.message}")

        headers = {}
        if "retry_after" in exc.details:
            headers["Retry-After"] = str(exc.details["retry_after"])

        return JSONResponse(
            status_code=429,
            content={
                "error_code": exc.error_code,
                "detail": exc.message,
                "details": exc.details,
                "request_id": request_id,
            },
            headers=headers,
        )

    # ============================================================
    # 標準例外ハンドラー
    # ============================================================

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            f"ValueError | request_id={request_id} | error={str(exc)}"
        )
        return JSONResponse(
            status_code=400,
            content={
                "error_code": "VALIDATION_ERROR",
                "detail": str(exc),
                "request_id": request_id,
            },
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            f"FileNotFoundError | request_id={request_id} | error={str(exc)}"
        )
        return JSONResponse(
            status_code=404,
            content={
                "error_code": "RESOURCE_NOT_FOUND",
                "detail": "Requested resource not found",
                "request_id": request_id,
            },
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            f"PermissionError | request_id={request_id} | error={str(exc)}"
        )
        return JSONResponse(
            status_code=403,
            content={
                "error_code": "PERMISSION_DENIED",
                "detail": "Permission denied",
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            f"Unhandled exception | request_id={request_id} | "
            f"type={type(exc).__name__} | error={str(exc)}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "detail": "Internal server error",
                "request_id": request_id,
            },
        )


def _get_status_code_for_exception(exc: PolicyReviewerException) -> int:
    """例外タイプに基づいてHTTPステータスコードを返す"""
    error_code_to_status = {
        "AUTHENTICATION_ERROR": 401,
        "AUTHORIZATION_ERROR": 403,
        "RESOURCE_NOT_FOUND": 404,
        "RESOURCE_CONFLICT": 409,
        "VALIDATION_ERROR": 400,
        "INVALID_INPUT": 400,
        "MISSING_REQUIRED_FIELD": 400,
        "SERVICE_UNAVAILABLE": 503,
        "RATE_LIMIT_EXCEEDED": 429,
        "DOCUMENT_PROCESSING_ERROR": 422,
        "OCR_ERROR": 422,
        "UNSUPPORTED_FILE_TYPE": 415,
        "FILE_TOO_LARGE": 413,
        "REVIEW_ERROR": 422,
        "EXTERNAL_SERVICE_ERROR": 502,
        "AZURE_OPENAI_ERROR": 502,
        "AZURE_DOC_INTEL_ERROR": 502,
        "DATABASE_ERROR": 500,
        "CONFIGURATION_ERROR": 500,
    }
    return error_code_to_status.get(exc.error_code, 500)
