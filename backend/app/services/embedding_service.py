"""
Unified Embedding Service for multi-cloud support.

マルチクラウドEmbeddingプロバイダーを統合するサービス。
Azure OpenAI, AWS Bedrock (Titan), GCP Vertex AI, Local (Ollama) に対応。

対応モデル:
    Azure OpenAI: text-embedding-3-large, text-embedding-3-small
    AWS Bedrock: amazon.titan-embed-text-v2:0
    GCP Vertex AI: text-embedding-005
    Local (Ollama): nomic-embed-text, mxbai-embed-large
"""

import json
import struct
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings, EmbeddingProvider

logger = logging.getLogger(__name__)


class BaseEmbeddingClient(ABC):
    """Embeddingクライアントの抽象基底クラス"""

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """テキストのEmbeddingベクトルを取得"""
        pass

    @abstractmethod
    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """複数テキストのEmbeddingベクトルを一括取得"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """クライアントが利用可能かチェック"""
        pass


class AzureOpenAIEmbeddingClient(BaseEmbeddingClient):
    """Azure OpenAI Embeddingクライアント"""

    def __init__(self):
        self.client = None
        self.deployment = settings.azure_openai_embedding_deployment
        self._initialize()

    def _initialize(self):
        if not settings.is_azure_configured():
            logger.warning("Azure OpenAI Embedding not configured")
            return
        try:
            from openai import AzureOpenAI

            self.client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
            logger.info(
                f"AzureOpenAIEmbeddingClient initialized | deployment={self.deployment}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI Embedding: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    async def get_embedding(self, text: str) -> list[float]:
        if not self.client:
            raise RuntimeError("Azure OpenAI Embedding not configured")
        response = self.client.embeddings.create(
            model=self.deployment,
            input=text,
        )
        return response.data[0].embedding

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        if not self.client:
            raise RuntimeError("Azure OpenAI Embedding not configured")
        response = self.client.embeddings.create(
            model=self.deployment,
            input=texts,
        )
        return [item.embedding for item in response.data]


class AWSBedrockEmbeddingClient(BaseEmbeddingClient):
    """AWS Bedrock Embedding クライアント (Titan Embed)"""

    def __init__(self):
        self.client = None
        self.model_id = settings.aws_bedrock_embedding_model
        self._initialize()

    def _initialize(self):
        if not settings.is_bedrock_configured():
            logger.warning("AWS Bedrock Embedding not configured")
            return
        try:
            import boto3

            self.client = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            logger.info(
                f"AWSBedrockEmbeddingClient initialized | model={self.model_id}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock Embedding: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    async def get_embedding(self, text: str) -> list[float]:
        if not self.client:
            raise RuntimeError("AWS Bedrock Embedding not configured")
        body = json.dumps({"inputText": text})
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        result = json.loads(response["body"].read())
        return result["embedding"]

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        # Titan Embed V2はバッチAPIを持たないため逐次処理
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings


class GCPVertexEmbeddingClient(BaseEmbeddingClient):
    """GCP Vertex AI Embeddingクライアント"""

    def __init__(self):
        self.model = None
        self.model_name = settings.gcp_vertex_embedding_model
        self._initialize()

    def _initialize(self):
        if not settings.is_vertex_configured():
            logger.warning("GCP Vertex AI Embedding not configured")
            return
        try:
            import google.auth

            if settings.gcp_credentials_path:
                import google.auth.transport.requests
                from google.oauth2 import service_account

                creds = service_account.Credentials.from_service_account_file(
                    settings.gcp_credentials_path
                )
            else:
                creds, _ = google.auth.default()

            import vertexai
            from vertexai.language_models import TextEmbeddingModel

            vertexai.init(
                project=settings.gcp_project_id,
                location=settings.gcp_location
                if settings.gcp_location != "global"
                else "us-central1",
                credentials=creds,
            )
            self.model = TextEmbeddingModel.from_pretrained(self.model_name)
            logger.info(
                f"GCPVertexEmbeddingClient initialized | model={self.model_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize GCP Vertex AI Embedding: {e}")

    def is_available(self) -> bool:
        return self.model is not None

    async def get_embedding(self, text: str) -> list[float]:
        if not self.model:
            raise RuntimeError("GCP Vertex AI Embedding not configured")
        embeddings = self.model.get_embeddings([text])
        return embeddings[0].values

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        if not self.model:
            raise RuntimeError("GCP Vertex AI Embedding not configured")
        # Vertex AIはバッチ対応（最大250テキスト）
        chunk_size = 250
        all_embeddings = []
        for i in range(0, len(texts), chunk_size):
            chunk = texts[i : i + chunk_size]
            embeddings = self.model.get_embeddings(chunk)
            all_embeddings.extend([e.values for e in embeddings])
        return all_embeddings


class OllamaEmbeddingClient(BaseEmbeddingClient):
    """Ollama (Local) Embeddingクライアント"""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_embedding_model
        self._available = False
        self._initialize()

    def _initialize(self):
        if not settings.is_ollama_configured():
            logger.warning("Ollama Embedding not configured")
            return
        self._available = True
        logger.info(
            f"OllamaEmbeddingClient initialized | url={self.base_url} | model={self.model}"
        )

    def is_available(self) -> bool:
        return self._available

    async def get_embedding(self, text: str) -> list[float]:
        if not self._available:
            raise RuntimeError("Ollama Embedding not configured")
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        # Ollamaは逐次処理
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings


class UnifiedEmbeddingService:
    """
    マルチプロバイダーEmbeddingサービス。

    設定に基づいて適切なプロバイダーを初期化し、
    統一インターフェースでEmbedding生成を提供する。
    """

    def __init__(self):
        self.clients: dict[EmbeddingProvider, BaseEmbeddingClient] = {}
        self.active_provider: Optional[EmbeddingProvider] = None
        self._initialize_clients()

    def _initialize_clients(self):
        """設定済みのEmbeddingクライアントを初期化"""
        # Azure OpenAI
        if settings.is_azure_configured():
            client = AzureOpenAIEmbeddingClient()
            if client.is_available():
                self.clients[EmbeddingProvider.AZURE_OPENAI] = client

        # AWS Bedrock
        if settings.is_bedrock_configured():
            client = AWSBedrockEmbeddingClient()
            if client.is_available():
                self.clients[EmbeddingProvider.AWS_BEDROCK] = client

        # GCP Vertex AI
        if settings.is_vertex_configured():
            client = GCPVertexEmbeddingClient()
            if client.is_available():
                self.clients[EmbeddingProvider.GCP_VERTEX] = client

        # Ollama (Local)
        if settings.is_ollama_configured():
            client = OllamaEmbeddingClient()
            if client.is_available():
                self.clients[EmbeddingProvider.LOCAL] = client

        # アクティブプロバイダー設定
        configured = settings.embedding_provider
        if configured in self.clients:
            self.active_provider = configured
        elif self.clients:
            self.active_provider = next(iter(self.clients))
            logger.warning(
                f"Configured embedding provider '{configured.value}' not available, "
                f"falling back to '{self.active_provider.value}'"
            )
        else:
            logger.warning("No embedding providers available")

        if self.active_provider:
            logger.info(
                f"UnifiedEmbeddingService initialized | "
                f"active={self.active_provider.value} | "
                f"available={[p.value for p in self.clients.keys()]}"
            )

    def is_available(self) -> bool:
        """Embeddingサービスが利用可能かチェック"""
        return self.active_provider is not None

    def set_provider(self, provider: EmbeddingProvider):
        """アクティブなEmbeddingプロバイダーを切り替え"""
        if provider not in self.clients:
            raise ValueError(
                f"Embedding provider '{provider.value}' is not available. "
                f"Available: {[p.value for p in self.clients.keys()]}"
            )
        self.active_provider = provider
        logger.info(f"Embedding provider switched to: {provider.value}")

    def _get_client(self) -> BaseEmbeddingClient:
        """アクティブなクライアントを取得"""
        if not self.active_provider:
            raise RuntimeError("No embedding providers configured")
        return self.clients[self.active_provider]

    async def get_embedding(self, text: str) -> list[float]:
        """
        テキストのEmbeddingベクトルを取得。

        Args:
            text: 埋め込みを生成するテキスト

        Returns:
            Embeddingベクトル (list[float])
        """
        client = self._get_client()
        start_time = time.time()
        try:
            embedding = await client.get_embedding(text)
            duration_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"Embedding generated | provider={self.active_provider.value} | "
                f"text_length={len(text)} | vector_dim={len(embedding)} | "
                f"duration_ms={duration_ms:.2f}"
            )
            return embedding
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Embedding failed | provider={self.active_provider.value} | "
                f"text_length={len(text)} | duration_ms={duration_ms:.2f} | "
                f"error={str(e)}"
            )
            raise

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        複数テキストのEmbeddingベクトルを一括取得。

        Args:
            texts: 埋め込みを生成するテキストのリスト

        Returns:
            Embeddingベクトルのリスト
        """
        client = self._get_client()
        start_time = time.time()
        try:
            embeddings = await client.get_embeddings_batch(texts)
            duration_ms = (time.time() - start_time) * 1000
            total_chars = sum(len(t) for t in texts)
            logger.debug(
                f"Batch embedding generated | provider={self.active_provider.value} | "
                f"count={len(texts)} | total_chars={total_chars} | "
                f"duration_ms={duration_ms:.2f}"
            )
            return embeddings
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Batch embedding failed | provider={self.active_provider.value} | "
                f"count={len(texts)} | duration_ms={duration_ms:.2f} | "
                f"error={str(e)}"
            )
            raise

    @staticmethod
    def embedding_to_bytes(embedding: list[float]) -> bytes:
        """Embeddingベクトルをbytes形式に変換（DB保存用）"""
        return struct.pack(f"{len(embedding)}f", *embedding)

    @staticmethod
    def bytes_to_embedding(data: bytes) -> list[float]:
        """bytes形式をEmbeddingベクトルに復元"""
        count = len(data) // 4  # float32 is 4 bytes
        return list(struct.unpack(f"{count}f", data))


# Singleton instance（後方互換性を維持）
embedding_service = UnifiedEmbeddingService()
