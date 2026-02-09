"""
FastAPI application entry point.
規程レビューツールのバックエンドAPIサーバー

Enterprise features:
- Prometheus metrics endpoint (/metrics)
- Request correlation ID tracking
- Structured logging with correlation context
- Circuit breaker integration
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, validate_and_log_config
from app.api import (
    auth,
    health,
    terms,
    check_items,
    writing_rules,
    documents,
    reviews,
    findings,
)
from app.db.init_db import create_tables
from app.core.logging_config import init_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware, add_exception_handlers
from app.core.observability.metrics import get_metrics, set_app_info
from app.core.observability.correlation import CorrelationMiddleware
from app.core.observability.audit import audit_logger, AuditEventType
from app.core.security.rate_limiter import RateLimitMiddleware
from app.core.security.headers import SecurityHeadersMiddleware

# ログ設定の初期化
init_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Application starting up...")

    # 設定の検証
    validate_and_log_config(logger)

    # データベースの初期化
    create_tables()
    logger.info("Database tables initialized")

    # メトリクス情報を設定
    environment = "development" if settings.debug else "production"
    set_app_info(
        version="0.2.0",
        environment=environment,
        llm_provider=settings.llm_provider.value,
    )
    logger.info(f"Metrics initialized | environment={environment}")

    # 監査ログ: システム起動
    audit_logger.log(
        event_type=AuditEventType.SYSTEM_START,
        resource_type="system",
        details={
            "version": "0.2.0",
            "environment": environment,
            "llm_provider": settings.llm_provider.value,
        },
    )

    yield

    # Shutdown
    logger.info("Application shutting down...")
    audit_logger.log(
        event_type=AuditEventType.SYSTEM_STOP,
        resource_type="system",
    )


app = FastAPI(
    title="規程レビューツール API",
    description="AI-powered policy document review system with enterprise features",
    version="0.2.0",
    lifespan=lifespan,
)

# Middleware (逆順で実行される - 最初に追加したものが最後に実行)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# セキュリティヘッダーミドルウェア
app.add_middleware(SecurityHeadersMiddleware, production=not settings.debug)

# レート制限ミドルウェア
app.add_middleware(RateLimitMiddleware)

# リクエストログミドルウェア
app.add_middleware(RequestLoggingMiddleware)

# 相関IDミドルウェア（最初に実行されるべき）
app.add_middleware(CorrelationMiddleware)

# グローバル例外ハンドラー
add_exception_handlers(app)

logger.info("Application initialized successfully")

# Include routers
app.include_router(auth.router)
app.include_router(health.router, tags=["Health"])
app.include_router(terms.router)
app.include_router(check_items.router)
app.include_router(writing_rules.router)
app.include_router(documents.router)
app.include_router(reviews.router)
app.include_router(findings.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "規程レビューツール API",
        "version": "0.2.0",
        "docs": "/docs",
        "metrics": "/metrics",
    }


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Prometheusスクレイピング用のメトリクスエンドポイント。
    """
    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)
