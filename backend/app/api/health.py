"""
Health check endpoints for Kubernetes probes and monitoring.

Kubernetesプローブおよび監視用のヘルスチェックエンドポイント。
- /health/live: Liveness probe（アプリケーションが動作中か）
- /health/ready: Readiness probe（トラフィック受信可能か）
- /health/detailed: 詳細ステータス（全依存関係の状態）
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.database import get_db
from app.config import settings
from app.core.resilience.circuit_breaker import get_all_breakers

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthStatus:
    """ヘルスステータス定数"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@router.get("/health")
async def health_check():
    """Basic health check endpoint (legacy compatibility)."""
    return {
        "status": HealthStatus.HEALTHY,
        "version": "0.2.0",
    }


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes Liveness Probe.

    アプリケーションが動作中かを確認。
    失敗時はKubernetesがコンテナを再起動する。
    """
    return {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
async def readiness_probe(
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Kubernetes Readiness Probe.

    トラフィックを受信可能かを確認。
    失敗時はKubernetesがサービスからPodを除外する。
    """
    checks = {
        "database": await _check_database(db),
    }

    # 全てのチェックが通過したらready
    all_healthy = all(c["healthy"] for c in checks.values())

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": HealthStatus.UNHEALTHY,
            "ready": False,
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "status": HealthStatus.HEALTHY,
        "ready": True,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health_check(
    response: Response,
    db: Session = Depends(get_db),
):
    """
    詳細ヘルスチェック。

    全ての依存関係とサーキットブレーカーの状態を返す。
    監視・デバッグ用。
    """
    # 各依存関係のチェックを並列実行
    db_check, llm_check, ocr_check = await asyncio.gather(
        _check_database(db),
        _check_llm_service(),
        _check_ocr_service(),
    )

    # サーキットブレーカーの状態を取得
    circuit_breakers = _get_circuit_breaker_status()

    # 全体のステータスを判定
    checks = {
        "database": db_check,
        "llm_service": llm_check,
        "ocr_service": ocr_check,
    }

    unhealthy_count = sum(1 for c in checks.values() if not c["healthy"])
    degraded_count = sum(
        1 for cb in circuit_breakers.values() if cb["state"] in ["open", "half_open"]
    )

    if unhealthy_count > 0:
        overall_status = HealthStatus.UNHEALTHY
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif degraded_count > 0:
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY

    return {
        "status": overall_status,
        "version": "0.2.0",
        "environment": "development" if settings.debug else "production",
        "checks": checks,
        "circuit_breakers": circuit_breakers,
        "configuration": {
            "llm_provider": settings.llm_provider.value,
            "llm_model": settings.get_effective_model(),
            "llm_tier": settings.llm_tier.value if settings.llm_tier else None,
            "azure_openai_configured": settings.is_azure_configured(),
            "aws_bedrock_configured": settings.is_bedrock_configured(),
            "gcp_vertex_configured": settings.is_vertex_configured(),
            "ollama_configured": settings.is_ollama_configured(),
            "ocr_provider": settings.ocr_provider.value,
            "azure_doc_intel_configured": settings.is_doc_intel_configured(),
            "tesseract_configured": settings.is_tesseract_configured(),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/db")
async def db_health_check(db: Session = Depends(get_db)):
    """Database connection health check (legacy compatibility)."""
    result = await _check_database(db)
    if result["healthy"]:
        return {
            "status": HealthStatus.HEALTHY,
            "database": "connected",
        }
    return {
        "status": HealthStatus.UNHEALTHY,
        "database": "disconnected",
        "error": result.get("error"),
    }


@router.get("/api/v1/system/info")
async def system_info():
    """Get system information."""
    return {
        "app_name": "規程レビューツール",
        "version": "0.2.0",
        "debug": settings.debug,
        "llm_provider": settings.llm_provider.value,
        "llm_model": settings.get_effective_model(),
        "llm_tier": settings.llm_tier.value if settings.llm_tier else None,
        "azure_openai_configured": settings.is_azure_configured(),
        "aws_bedrock_configured": settings.is_bedrock_configured(),
        "gcp_vertex_configured": settings.is_vertex_configured(),
        "ollama_configured": settings.is_ollama_configured(),
        "ocr_provider": settings.ocr_provider.value,
        "azure_doc_intel_configured": settings.is_doc_intel_configured(),
        "tesseract_configured": settings.is_tesseract_configured(),
    }


# =============================================================================
# Internal Health Check Functions
# =============================================================================


async def _check_database(db: Session) -> Dict[str, Any]:
    """データベース接続をチェック"""
    try:
        db.execute(text("SELECT 1"))
        return {
            "healthy": True,
            "latency_ms": 0,  # 実際の計測は省略
        }
    except Exception as e:
        logger.warning(f"Database health check failed: {str(e)}")
        return {
            "healthy": False,
            "error": str(e)[:100],
        }


async def _check_llm_service() -> Dict[str, Any]:
    """LLMサービスの状態をチェック"""
    try:
        from app.services.llm_service import llm_service

        available = llm_service.is_available()
        providers = llm_service.get_available_providers()

        return {
            "healthy": available,
            "active_provider": (
                llm_service.active_provider.value
                if llm_service.active_provider
                else None
            ),
            "available_providers": [p.value for p in providers],
        }
    except Exception as e:
        logger.warning(f"LLM service health check failed: {str(e)}")
        return {
            "healthy": False,
            "error": str(e)[:100],
        }


async def _check_ocr_service() -> Dict[str, Any]:
    """OCRサービスの状態をチェック（マルチプロバイダー対応）"""
    try:
        from app.services.ocr_service import ocr_service, OCRServiceFactory

        active_provider = settings.ocr_provider.value
        available_providers = [
            p.value for p in OCRServiceFactory.get_available_providers()
        ]
        is_available = ocr_service.is_available()

        return {
            "healthy": True,  # OCR未設定でもアプリは動作可能
            "active_provider": active_provider,
            "available_providers": available_providers,
            "configured": is_available,
            "note": (
                None
                if is_available
                else "OCR service not configured, PDF extraction may be limited"
            ),
        }
    except Exception as e:
        logger.warning(f"OCR service health check failed: {str(e)}")
        return {
            "healthy": True,
            "configured": False,
            "error": str(e)[:100],
        }


def _get_circuit_breaker_status() -> Dict[str, Any]:
    """全サーキットブレーカーの状態を取得"""
    breakers = get_all_breakers()
    status = {}

    for name, breaker in breakers.items():
        breaker_status = breaker.get_status()
        status[name] = {
            "state": breaker_status["state"],
            "failure_count": breaker_status["failure_count"],
            "time_until_retry": breaker_status["time_until_retry"],
            "stats": {
                "total_calls": breaker_status["stats"]["total_calls"],
                "failed_calls": breaker_status["stats"]["failed_calls"],
                "rejected_calls": breaker_status["stats"]["rejected_calls"],
            },
        }

    return status
