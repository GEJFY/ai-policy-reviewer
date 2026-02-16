"""Vector store service for similarity search."""

import logging
import struct
import math
from typing import Optional
from sqlalchemy.orm import Session

from app.models.term import Term
from app.models.document import DocumentChunk
from app.services.embedding_service import UnifiedEmbeddingService

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Service for vector similarity search.

    Note: This implementation uses cosine similarity calculation in Python.
    For production, consider using sqlite-vec extension or Chromadb.
    """

    def __init__(self, embedding_service: Optional[UnifiedEmbeddingService] = None):
        """Initialize vector store."""
        self.embedding_service = embedding_service

    @staticmethod
    def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def search_similar_terms(
        self,
        db: Session,
        query_embedding: list[float],
        top_k: int = 10,
        category: Optional[str] = None,
    ) -> list[tuple[Term, float]]:
        """
        Search for similar terms using cosine similarity.

        Args:
            db: Database session
            query_embedding: Query embedding vector
            top_k: Number of results to return
            category: Optional category filter

        Returns:
            List of (term, similarity_score) tuples
        """
        try:
            # Query terms with embeddings
            query = db.query(Term).filter(Term.embedding.isnot(None))
            if category:
                query = query.filter(Term.category == category)

            terms = query.all()

            # Calculate similarities
            results = []
            for term in terms:
                try:
                    term_embedding = self._bytes_to_embedding(term.embedding)
                    similarity = self.cosine_similarity(query_embedding, term_embedding)
                    results.append((term, similarity))
                except (struct.error, ValueError) as e:
                    logger.warning(
                        f"Skipping term with invalid embedding | "
                        f"term_id={term.id} | error={e}"
                    )

            # Sort by similarity (descending) and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"Term similarity search failed | error={e}")
            return []

    def search_similar_chunks(
        self,
        db: Session,
        query_embedding: list[float],
        document_id: Optional[int] = None,
        top_k: int = 10,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search for similar document chunks using cosine similarity.

        Args:
            db: Database session
            query_embedding: Query embedding vector
            document_id: Optional document filter
            top_k: Number of results to return

        Returns:
            List of (chunk, similarity_score) tuples
        """
        try:
            # Query chunks with embeddings
            query = db.query(DocumentChunk).filter(DocumentChunk.embedding.isnot(None))
            if document_id:
                query = query.filter(DocumentChunk.document_id == document_id)

            chunks = query.all()

            # Calculate similarities
            results = []
            for chunk in chunks:
                try:
                    chunk_embedding = self._bytes_to_embedding(chunk.embedding)
                    similarity = self.cosine_similarity(
                        query_embedding, chunk_embedding
                    )
                    results.append((chunk, similarity))
                except (struct.error, ValueError) as e:
                    logger.warning(
                        f"Skipping chunk with invalid embedding | "
                        f"chunk_id={chunk.id} | error={e}"
                    )

            # Sort by similarity (descending) and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"Chunk similarity search failed | error={e}")
            return []

    @staticmethod
    def _bytes_to_embedding(data: bytes) -> list[float]:
        """Convert bytes to embedding vector."""
        count = len(data) // 4
        return list(struct.unpack(f"{count}f", data))

    @staticmethod
    def _embedding_to_bytes(embedding: list[float]) -> bytes:
        """Convert embedding vector to bytes."""
        return struct.pack(f"{len(embedding)}f", *embedding)


# Singleton instance
vector_store = VectorStore()
