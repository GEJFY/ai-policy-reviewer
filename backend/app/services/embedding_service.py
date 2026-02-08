"""
Embedding service using Azure OpenAI.
テキストをベクトル化して類似度検索を可能にする
"""

import struct
import time
import logging
from typing import Optional
from openai import AzureOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using Azure OpenAI."""

    def __init__(self):
        """Initialize the embedding service."""
        self.client: Optional[AzureOpenAI] = None
        self.deployment = settings.azure_openai_embedding_deployment
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Azure OpenAI client if configured."""
        if settings.azure_openai_endpoint and settings.azure_openai_api_key:
            self.client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
            logger.info(f"EmbeddingService initialized | deployment={self.deployment}")
        else:
            logger.warning("EmbeddingService not configured - missing Azure credentials")

    def is_available(self) -> bool:
        """Check if embedding service is available."""
        return self.client is not None

    async def get_embedding(self, text: str) -> list[float]:
        """
        Get embedding vector for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not self.client:
            logger.error("Embedding service not configured")
            raise RuntimeError("Embedding service not configured")

        start_time = time.time()
        try:
            response = self.client.embeddings.create(
                model=self.deployment,
                input=text,
            )
            duration_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"Embedding generated | text_length={len(text)} | "
                f"vector_dim={len(response.data[0].embedding)} | "
                f"duration_ms={duration_ms:.2f}"
            )
            return response.data[0].embedding
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Embedding generation failed | text_length={len(text)} | "
                f"duration_ms={duration_ms:.2f} | error={str(e)}"
            )
            raise

    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Get embedding vectors for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self.client:
            logger.error("Embedding service not configured")
            raise RuntimeError("Embedding service not configured")

        start_time = time.time()
        try:
            response = self.client.embeddings.create(
                model=self.deployment,
                input=texts,
            )
            duration_ms = (time.time() - start_time) * 1000
            total_chars = sum(len(t) for t in texts)
            logger.debug(
                f"Batch embedding generated | count={len(texts)} | "
                f"total_chars={total_chars} | duration_ms={duration_ms:.2f}"
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Batch embedding generation failed | count={len(texts)} | "
                f"duration_ms={duration_ms:.2f} | error={str(e)}"
            )
            raise

    @staticmethod
    def embedding_to_bytes(embedding: list[float]) -> bytes:
        """
        Convert embedding vector to bytes for storage.

        Args:
            embedding: List of floats

        Returns:
            Bytes representation
        """
        return struct.pack(f"{len(embedding)}f", *embedding)

    @staticmethod
    def bytes_to_embedding(data: bytes) -> list[float]:
        """
        Convert bytes back to embedding vector.

        Args:
            data: Bytes representation

        Returns:
            List of floats
        """
        count = len(data) // 4  # float32 is 4 bytes
        return list(struct.unpack(f"{count}f", data))


# Singleton instance
embedding_service = EmbeddingService()
