"""Text chunking service for document processing."""

import re
from typing import Optional

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class ChunkingService:
    """Service for chunking text documents with overlap."""

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        encoding_name: str = "cl100k_base",
    ):
        """
        Initialize the chunking service.

        Args:
            chunk_size: Target chunk size in tokens
            overlap: Overlap between chunks in tokens
            encoding_name: Tokenizer encoding name
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = None

        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.get_encoding(encoding_name)
            except Exception:
                pass

    def chunk_text(self, text: str) -> list[str]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        # If tiktoken is available, use token-based chunking
        if self.tokenizer:
            return self._chunk_by_tokens(text)

        # Fallback to character-based chunking
        return self._chunk_by_characters(text)

    def _chunk_by_tokens(self, text: str) -> list[str]:
        """Chunk by token count."""
        tokens = self.tokenizer.encode(text)
        chunks = []

        start = 0
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)

            if end >= len(tokens):
                break

            start = end - self.overlap

        return chunks

    def _chunk_by_characters(self, text: str, chars_per_token: int = 4) -> list[str]:
        """Fallback character-based chunking."""
        char_chunk_size = self.chunk_size * chars_per_token
        char_overlap = self.overlap * chars_per_token
        chunks = []

        start = 0
        while start < len(text):
            end = min(start + char_chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)

            if end >= len(text):
                break

            start = end - char_overlap

        return chunks

    def chunk_by_sections(
        self,
        text: str,
        section_pattern: Optional[str] = None,
    ) -> list[dict]:
        """
        Chunk text by sections (e.g., articles in regulations).

        Args:
            text: Text to chunk
            section_pattern: Regex pattern to identify section starts

        Returns:
            List of dicts with section info and content
        """
        if not section_pattern:
            # Default pattern for Japanese regulations
            section_pattern = r"(第[一二三四五六七八九十百千]+条|第\d+条)"

        sections = []
        matches = list(re.finditer(section_pattern, text))

        if not matches:
            # No sections found, return whole text as single chunk
            return [{"section": "全文", "content": text, "start": 0, "end": len(text)}]

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            section_text = text[start:end].strip()
            section_name = match.group(1)

            sections.append(
                {
                    "section": section_name,
                    "content": section_text,
                    "start": start,
                    "end": end,
                }
            )

        return sections


# Singleton instance
chunking_service = ChunkingService()
