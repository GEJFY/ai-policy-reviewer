"""
Settings API endpoints.

現在のアプリケーション設定の表示用エンドポイント。
シークレット情報はマスクして返す。
"""

import re
from typing import Any

from fastapi import APIRouter

from app.config import settings, MODEL_TIER_DEFAULTS, LLMProvider

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


def _mask_secret(value: str) -> str:
    """シークレット値をマスクする（末尾4文字のみ表示）。"""
    if not value or len(value) < 8:
        return "***" if value else ""
    return f"***{value[-4:]}"


def _mask_url_key(url: str) -> str:
    """URL内のAPIキーパラメータをマスクする。"""
    if not url:
        return ""
    # URLパス内のキーっぽいパターンをマスク
    return re.sub(r"(key|token|secret)=[^&]+", r"\1=***", url, flags=re.IGNORECASE)


@router.get("/")
async def get_settings() -> dict[str, Any]:
    """
    現在の設定を返す（シークレットはマスク済み）。

    プロバイダー設定、OCR設定、アプリ設定を含む。
    """
    config_status = settings.validate_config()

    return {
        "system": {
            "version": "0.2.0",
            "debug": settings.debug,
            "database_url": _mask_database_url(settings.database_url),
        },
        "llm": {
            "provider": settings.llm_provider.value,
            "model": settings.get_effective_model(),
            "tier": settings.llm_tier.value if settings.llm_tier else None,
            "available_providers": [
                p.value for p in settings.get_available_providers()
            ],
        },
        "providers": {
            "azure": {
                "configured": settings.is_azure_configured(),
                "endpoint": _mask_url_key(settings.azure_openai_endpoint),
                "api_key": _mask_secret(settings.azure_openai_api_key),
                "deployment": settings.azure_openai_deployment,
                "embedding_deployment": settings.azure_openai_embedding_deployment,
                "api_version": settings.azure_openai_api_version,
                "use_v1_api": settings.azure_openai_use_v1_api,
            },
            "aws_bedrock": {
                "configured": settings.is_bedrock_configured(),
                "region": settings.aws_region,
                "access_key_id": _mask_secret(settings.aws_access_key_id),
                "model_id": settings.aws_bedrock_model_id,
                "embedding_model": settings.aws_bedrock_embedding_model,
            },
            "gcp_vertex": {
                "configured": settings.is_vertex_configured(),
                "project_id": settings.gcp_project_id,
                "location": settings.gcp_location,
                "model": settings.gcp_vertex_model,
                "embedding_model": settings.gcp_vertex_embedding_model,
                "credentials_path": bool(settings.gcp_credentials_path),
            },
            "ollama": {
                "configured": settings.is_ollama_configured(),
                "base_url": settings.ollama_base_url,
                "model": settings.ollama_model,
                "embedding_model": settings.ollama_embedding_model,
            },
        },
        "embedding": {
            "provider": settings.embedding_provider.value,
        },
        "ocr": {
            "provider": settings.ocr_provider.value,
            "azure_doc_intel": {
                "configured": settings.is_doc_intel_configured(),
                "endpoint": _mask_url_key(settings.azure_doc_intel_endpoint),
            },
            "tesseract": {
                "configured": settings.is_tesseract_configured(),
                "lang": settings.tesseract_lang,
            },
        },
        "app": {
            "upload_dir": settings.upload_dir,
            "max_file_size_mb": settings.max_file_size_mb,
            "cors_origins": settings.cors_origins,
        },
        "validation": {
            "is_valid": config_status.is_valid,
            "missing": config_status.missing,
            "warnings": config_status.warnings,
        },
    }


@router.get("/models")
async def get_available_models() -> dict[str, Any]:
    """
    プロバイダーごとの利用可能モデル一覧を返す。
    """
    models: dict[str, list[dict[str, str]]] = {}

    for provider in LLMProvider:
        tier_defaults = MODEL_TIER_DEFAULTS.get(provider, {})
        models[provider.value] = [
            {"tier": tier.value, "model": model}
            for tier, model in tier_defaults.items()
        ]

    return {"models": models}


def _mask_database_url(url: str) -> str:
    """DB接続文字列内のパスワードをマスクする。"""
    if not url:
        return ""
    # sqlite:///... はそのまま返す
    if url.startswith("sqlite"):
        return url
    # postgresql://user:password@host/db → マスク
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)
