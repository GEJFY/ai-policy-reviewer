"""
Application configuration management.

環境変数から設定を読み込み、アプリケーション全体で使用する。
起動時に設定の妥当性を検証し、不足している設定を警告する。
マルチクラウドLLMプロバイダー（Azure, AWS Bedrock, GCP Vertex AI, Local/Ollama）対応。
"""

import logging
from enum import Enum
from functools import lru_cache
from typing import Optional, NamedTuple
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    """LLMプロバイダーの種類"""
    AZURE = "azure"
    AWS_BEDROCK = "aws_bedrock"
    GCP_VERTEX = "gcp_vertex"
    LOCAL = "local"  # Ollama


class ModelTier(str, Enum):
    """モデルのティア（精度・コストのバランス）"""
    PRECISION = "precision"           # 最高精度、高コスト
    BALANCED = "balanced"             # バランス型
    COST_EFFECTIVE = "cost_effective"  # コスト重視


class OCRProvider(str, Enum):
    """OCRプロバイダーの種類"""
    AZURE_DOC_INTEL = "azure_doc_intel"
    TESSERACT = "tesseract"
    AWS_TESSERACT = "aws_tesseract"


class LLMModel(str, Enum):
    """利用可能なLLMモデル（2026年2月時点）"""
    # === Azure AI Foundry Models ===
    # Precision
    GPT_5_2 = "gpt-5.2"
    GPT_5_2_CODEX = "gpt-5.2-codex"
    AZURE_CLAUDE_OPUS = "claude-opus-4-6"
    # Balanced
    GPT_5_MINI = "gpt-5-mini"
    AZURE_CLAUDE_SONNET = "claude-sonnet-4-5"
    # Cost-effective
    GPT_5_NANO = "gpt-5-nano"
    AZURE_CLAUDE_HAIKU = "claude-haiku-4-5"
    # Legacy
    GPT_4O = "gpt-4o"

    # === AWS Bedrock Models ===
    # Precision
    BEDROCK_CLAUDE_OPUS = "us.anthropic.claude-opus-4-6-v1"
    BEDROCK_NOVA_PREMIER = "us.amazon.nova-premier-v1:0"
    # Balanced
    BEDROCK_CLAUDE_SONNET = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    BEDROCK_NOVA_PRO = "us.amazon.nova-pro-v1:0"
    BEDROCK_LLAMA4_MAVERICK = "us.meta.llama4-maverick-17b-instruct-v1:0"
    # Cost-effective
    BEDROCK_CLAUDE_HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    BEDROCK_NOVA_MICRO = "us.amazon.nova-micro-v1:0"
    BEDROCK_NOVA_LITE = "us.amazon.nova-lite-v1:0"

    # === GCP Vertex AI Models ===
    # Precision
    GEMINI_3_PRO = "gemini-3-pro-preview"
    VERTEX_CLAUDE_OPUS = "claude-opus-4-6"
    # Balanced
    GEMINI_3_FLASH = "gemini-3-flash-preview"
    VERTEX_CLAUDE_SONNET = "claude-sonnet-4-5"
    # Cost-effective
    VERTEX_CLAUDE_HAIKU = "claude-haiku-4-5"

    # === Local (Ollama) Models ===
    OLLAMA_QWEN25_3B = "qwen2.5:3b"
    OLLAMA_GEMMA2_JPN = "schroneko/gemma-2-2b-jpn-it"
    OLLAMA_QWEN25_05B = "qwen2.5:0.5b"


# プロバイダー × ティア → デフォルトモデルのマッピング
MODEL_TIER_DEFAULTS: dict[LLMProvider, dict[ModelTier, str]] = {
    LLMProvider.AZURE: {
        ModelTier.PRECISION: "gpt-5.2",
        ModelTier.BALANCED: "gpt-5-mini",
        ModelTier.COST_EFFECTIVE: "gpt-5-nano",
    },
    LLMProvider.AWS_BEDROCK: {
        ModelTier.PRECISION: "us.anthropic.claude-opus-4-6-v1",
        ModelTier.BALANCED: "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        ModelTier.COST_EFFECTIVE: "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    },
    LLMProvider.GCP_VERTEX: {
        ModelTier.PRECISION: "gemini-3-pro-preview",
        ModelTier.BALANCED: "gemini-3-flash-preview",
        ModelTier.COST_EFFECTIVE: "claude-haiku-4-5",
    },
    LLMProvider.LOCAL: {
        ModelTier.PRECISION: "qwen2.5:3b",
        ModelTier.BALANCED: "qwen2.5:3b",
        ModelTier.COST_EFFECTIVE: "schroneko/gemma-2-2b-jpn-it",
    },
}


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
    llm_tier: Optional[ModelTier] = None  # ティア指定（Noneの場合llm_modelを直接使用）

    # Azure OpenAI / Azure Foundry (v1 API対応)
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-5-2"  # GPT-5.2デプロイメント名
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    azure_openai_api_version: str = "2024-08-01-preview"
    azure_openai_use_v1_api: bool = True  # v1 API使用フラグ

    # AWS Bedrock
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_bedrock_model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # GCP Vertex AI
    gcp_project_id: str = ""
    gcp_location: str = "global"  # Gemini 3はglobalエンドポイントのみ
    gcp_credentials_path: str = ""  # サービスアカウントJSONパス
    gcp_vertex_model: str = "gemini-3-flash-preview"

    # Local LLM (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "schroneko/gemma-2-2b-jpn-it"

    # Azure Document Intelligence
    azure_doc_intel_endpoint: str = ""
    azure_doc_intel_key: str = ""

    # OCR Provider Selection
    ocr_provider: OCRProvider = OCRProvider.AZURE_DOC_INTEL

    # Tesseract (Local)
    tesseract_path: str = ""  # 空の場合PATH環境変数を検索
    tesseract_lang: str = "jpn+eng"

    # AWS Tesseract (Remote)
    aws_tesseract_endpoint: str = ""

    # App
    secret_key: str = "dev-secret-key"
    debug: bool = True

    # CORS (ポート3030に変更)
    cors_origins: list[str] = ["http://localhost:3030"]

    class Config:
        env_file = (".env", "../.env")  # backend/.env → project root/.env
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
        elif self.llm_provider == LLMProvider.LOCAL:
            if not self.ollama_base_url:
                missing.append("OLLAMA_BASE_URL")

        # OCRプロバイダー別の設定チェック
        if self.ocr_provider == OCRProvider.AZURE_DOC_INTEL:
            if not self.azure_doc_intel_endpoint:
                warnings.append("AZURE_DOC_INTEL_ENDPOINT - OCR機能が制限されます")
            if not self.azure_doc_intel_key:
                warnings.append("AZURE_DOC_INTEL_KEY - OCR機能が制限されます")
        elif self.ocr_provider == OCRProvider.AWS_TESSERACT:
            if not self.aws_tesseract_endpoint:
                missing.append("AWS_TESSERACT_ENDPOINT")

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

    def is_ollama_configured(self) -> bool:
        """Ollama (Local LLM) が設定されているかチェック。"""
        return bool(self.ollama_base_url)

    def is_openai_configured(self) -> bool:
        """Azure OpenAIが設定されているかチェック（後方互換性）。"""
        return self.is_azure_configured()

    def is_doc_intel_configured(self) -> bool:
        """Azure Document Intelligenceが設定されているかチェック。"""
        return bool(self.azure_doc_intel_endpoint and self.azure_doc_intel_key)

    def is_tesseract_configured(self) -> bool:
        """ローカルTesseractが利用可能かチェック。"""
        if self.tesseract_path:
            return True
        return self.ocr_provider == OCRProvider.TESSERACT

    def is_aws_tesseract_configured(self) -> bool:
        """AWS Tesseractエンドポイントが設定されているかチェック。"""
        return bool(self.aws_tesseract_endpoint)

    def get_effective_model(self) -> str:
        """
        実効モデル名を取得。
        llm_tierが設定されている場合、プロバイダーのティア対応モデルを返す。
        llm_modelが明示的に変更されている場合はそちらを優先。
        """
        if self.llm_tier:
            tier_defaults = MODEL_TIER_DEFAULTS.get(self.llm_provider, {})
            return tier_defaults.get(self.llm_tier, self.llm_model)
        return self.llm_model

    def get_available_providers(self) -> list[LLMProvider]:
        """設定済みの利用可能なプロバイダーを返す。"""
        providers = []
        if self.is_azure_configured():
            providers.append(LLMProvider.AZURE)
        if self.is_bedrock_configured():
            providers.append(LLMProvider.AWS_BEDROCK)
        if self.is_vertex_configured():
            providers.append(LLMProvider.GCP_VERTEX)
        if self.is_ollama_configured():
            providers.append(LLMProvider.LOCAL)
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
        logger.info(f"Active LLM Model: {settings.get_effective_model()}")

        if settings.llm_tier:
            logger.info(f"LLM Tier: {settings.llm_tier.value}")

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
        if settings.is_ollama_configured():
            logger.info(f"Ollama (Local): Configured | url={settings.ollama_base_url}")

        # OCR情報
        logger.info(f"Active OCR Provider: {settings.ocr_provider.value}")
        if settings.is_doc_intel_configured():
            logger.info("Azure Document Intelligence: Configured")
        else:
            logger.info("Azure Document Intelligence: Not configured")

    return status.is_valid


settings = get_settings()
