"""
Application configuration management.

環境変数から設定を読み込み、アプリケーション全体で使用する。
起動時に設定の妥当性を検証し、不足している設定を警告する。
マルチクラウドLLMプロバイダー（Azure, AWS Bedrock, GCP Vertex AI）対応。
"""

import logging
from enum import Enum
from functools import lru_cache
from typing import NamedTuple
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    """LLMプロバイダーの種類"""
    AZURE = "azure"
    AWS_BEDROCK = "aws_bedrock"
    GCP_VERTEX = "gcp_vertex"


class LLMModel(str, Enum):
    """利用可能なLLMモデル"""
    # Azure Foundry Models
    GPT_5_2 = "gpt-5.2"
    GPT_5_NANO = "gpt-5-nano"
    AZURE_CLAUDE_SONNET = "claude-sonnet-4"
    AZURE_CLAUDE_OPUS = "claude-opus-4"
    GPT_4O = "gpt-4o"  # 旧モデル（後方互換性）

    # AWS Bedrock Models
    BEDROCK_CLAUDE_SONNET_4_6 = "anthropic.claude-sonnet-4-6"
    BEDROCK_CLAUDE_OPUS = "anthropic.claude-opus-4"

    # GCP Vertex AI Models
    GEMINI_3_FLASH = "gemini-3.0-flash-preview"
    GEMINI_3_PRO = "gemini-3.0-pro-preview"


class ConfigStatus(NamedTuple):
    """設定の検証結果を表す。"""
    is_valid: bool
    missing: list[str]
    warnings: list[str]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///./data/policy_review.db"

    # LLM Provider Selection
    llm_provider: LLMProvider = LLMProvider.AZURE
    llm_model: str = "gpt-5.2"  # デフォルトは最新のGPT-5.2

    # Azure OpenAI / Azure Foundry (v1 API対応)
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-5-2"  # GPT-5.2デプロイメント名
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    azure_openai_use_v1_api: bool = True  # v1 API使用フラグ

    # AWS Bedrock
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_bedrock_model_id: str = "anthropic.claude-sonnet-4-6"  # 最新Claude

    # GCP Vertex AI
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    gcp_credentials_path: str = ""  # サービスアカウントJSONパス
    gcp_vertex_model: str = "gemini-3.0-flash-preview"

    # Azure Document Intelligence
    azure_doc_intel_endpoint: str = ""
    azure_doc_intel_key: str = ""

    # App
    secret_key: str = "dev-secret-key"
    debug: bool = True

    # CORS (ポート3030に変更)
    cors_origins: list[str] = ["http://localhost:3030"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def validate_config(self) -> ConfigStatus:
        """
        設定の妥当性を検証する。

        Returns:
            ConfigStatus: 検証結果（is_valid, missing, warnings）
        """
        missing = []
        warnings = []

        # LLMプロバイダー別の設定チェック
        if self.llm_provider == LLMProvider.AZURE:
            if not self.azure_openai_endpoint:
                missing.append("AZURE_OPENAI_ENDPOINT")
            if not self.azure_openai_api_key:
                missing.append("AZURE_OPENAI_API_KEY")
        elif self.llm_provider == LLMProvider.AWS_BEDROCK:
            if not self.aws_access_key_id:
                missing.append("AWS_ACCESS_KEY_ID")
            if not self.aws_secret_access_key:
                missing.append("AWS_SECRET_ACCESS_KEY")
        elif self.llm_provider == LLMProvider.GCP_VERTEX:
            if not self.gcp_project_id:
                missing.append("GCP_PROJECT_ID")
            if not self.gcp_credentials_path:
                warnings.append("GCP_CREDENTIALS_PATH - ADC認証を使用します")

        # Azure Document Intelligence設定チェック
        if not self.azure_doc_intel_endpoint:
            warnings.append("AZURE_DOC_INTEL_ENDPOINT - OCR機能が制限されます")
        if not self.azure_doc_intel_key:
            warnings.append("AZURE_DOC_INTEL_KEY - OCR機能が制限されます")

        # セキュリティ警告
        if self.secret_key == "dev-secret-key" and not self.debug:
            warnings.append("SECRET_KEY - 本番環境ではデフォルト値を使用しないでください")

        is_valid = len(missing) == 0
        return ConfigStatus(is_valid=is_valid, missing=missing, warnings=warnings)

    def is_azure_configured(self) -> bool:
        """Azure OpenAI/Foundryが設定されているかチェック。"""
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)

    def is_bedrock_configured(self) -> bool:
        """AWS Bedrockが設定されているかチェック。"""
        return bool(self.aws_access_key_id and self.aws_secret_access_key)

    def is_vertex_configured(self) -> bool:
        """GCP Vertex AIが設定されているかチェック。"""
        return bool(self.gcp_project_id)

    def is_openai_configured(self) -> bool:
        """Azure OpenAIが設定されているかチェック（後方互換性）。"""
        return self.is_azure_configured()

    def is_doc_intel_configured(self) -> bool:
        """Azure Document Intelligenceが設定されているかチェック。"""
        return bool(self.azure_doc_intel_endpoint and self.azure_doc_intel_key)

    def get_available_providers(self) -> list[LLMProvider]:
        """設定済みの利用可能なプロバイダーを返す。"""
        providers = []
        if self.is_azure_configured():
            providers.append(LLMProvider.AZURE)
        if self.is_bedrock_configured():
            providers.append(LLMProvider.AWS_BEDROCK)
        if self.is_vertex_configured():
            providers.append(LLMProvider.GCP_VERTEX)
        return providers


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def validate_and_log_config(logger: logging.Logger) -> bool:
    """
    設定を検証し、結果をログに出力する。

    Args:
        logger: ログ出力用のロガー

    Returns:
        bool: 設定が有効な場合True
    """
    status = settings.validate_config()

    if status.missing:
        logger.error(
            f"Required configuration missing: {', '.join(status.missing)}"
        )
        logger.error(
            "Please set the required environment variables in .env file"
        )

    if status.warnings:
        for warning in status.warnings:
            logger.warning(f"Configuration warning: {warning}")

    if status.is_valid:
        logger.info("Configuration validated successfully")
        logger.info(f"Active LLM Provider: {settings.llm_provider.value}")
        logger.info(f"Active LLM Model: {settings.llm_model}")

        # 利用可能なプロバイダーをログ出力
        available = settings.get_available_providers()
        if available:
            provider_names = [p.value for p in available]
            logger.info(f"Available providers: {', '.join(provider_names)}")

        if settings.is_azure_configured():
            logger.info("Azure OpenAI/Foundry: Configured")
        if settings.is_bedrock_configured():
            logger.info("AWS Bedrock: Configured")
        if settings.is_vertex_configured():
            logger.info("GCP Vertex AI: Configured")
        if settings.is_doc_intel_configured():
            logger.info("Azure Document Intelligence: Configured")
        else:
            logger.info("Azure Document Intelligence: Not configured (using PyPDF2 fallback)")

    return status.is_valid


settings = get_settings()
