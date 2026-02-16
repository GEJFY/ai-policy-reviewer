"""Text chunking service for document processing.

階層的チャンキング対応:
- セクション分割（条文単位）→ 大きなセクションはさらにサブチャンク
- セクションタイトル保持
- トークンベース + 文字ベースフォールバック
"""

import re
from typing import Optional

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class ChunkResult:
    """チャンク結果。セクションタイトル付き。"""

    __slots__ = ("content", "section_title")

    def __init__(self, content: str, section_title: Optional[str] = None):
        self.content = content
        self.section_title = section_title


class ChunkingService:
    """Service for chunking text documents with overlap."""

    # Japanese regulation section patterns (priority order)
    SECTION_PATTERNS = [
        # Chapter/Section headers
        r"(第[一二三四五六七八九十百千]+章|第\d+章)",
        # Article headers
        r"(第[一二三四五六七八九十百千]+条|第\d+条)",
        # Numbered section headers (1. 2. etc.)
        r"(?:^|\n)((?:\d+[\.．])\s*.+)",
    ]

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        encoding_name: str = "cl100k_base",
    ):
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
        Chunk text into overlapping segments (flat, no section info).

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        if self.tokenizer:
            return self._chunk_by_tokens(text)

        return self._chunk_by_characters(text)

    def chunk_text_hierarchical(self, text: str) -> list[ChunkResult]:
        """
        Hierarchical chunking: section-aware splitting with sub-chunking.

        1. Detect section boundaries (articles/chapters)
        2. Keep small sections as single chunks
        3. Sub-chunk large sections with overlap

        Args:
            text: Text to chunk

        Returns:
            List of ChunkResult with section_title metadata
        """
        if not text or not text.strip():
            return []

        # Try section-based chunking
        sections = self._detect_sections(text)

        if len(sections) <= 1 and len(sections[0]["content"]) == len(text.strip()):
            # No sections detected, fall back to flat chunking
            flat_chunks = self.chunk_text(text)
            return [ChunkResult(content=c, section_title=None) for c in flat_chunks]

        results: list[ChunkResult] = []
        for section in sections:
            section_content = section["content"]
            section_title = section["section"]
            token_count = self._count_tokens(section_content)

            if token_count <= self.chunk_size:
                # Section fits in one chunk
                results.append(
                    ChunkResult(
                        content=section_content,
                        section_title=section_title,
                    )
                )
            else:
                # Sub-chunk large sections
                sub_chunks = self.chunk_text(section_content)
                for i, sub in enumerate(sub_chunks):
                    suffix = (
                        f" ({i + 1}/{len(sub_chunks)})" if len(sub_chunks) > 1 else ""
                    )
                    results.append(
                        ChunkResult(
                            content=sub,
                            section_title=f"{section_title}{suffix}",
                        )
                    )

        return results

    def _detect_sections(self, text: str) -> list[dict]:
        """
        Detect section boundaries using multiple patterns.

        Tries chapter → article → numbered patterns.
        Returns the first pattern that produces meaningful splits.
        """
        for pattern in self.SECTION_PATTERNS:
            sections = self._split_by_pattern(text, pattern)
            if len(sections) > 1:
                return sections

        # No pattern matched
        return [
            {"section": None, "content": text.strip(), "start": 0, "end": len(text)}
        ]

    def _split_by_pattern(self, text: str, pattern: str) -> list[dict]:
        """Split text by regex pattern into sections."""
        matches = list(re.finditer(pattern, text))
        if not matches:
            return [
                {"section": None, "content": text.strip(), "start": 0, "end": len(text)}
            ]

        sections = []

        # Text before first match (preamble)
        if matches[0].start() > 0:
            preamble = text[: matches[0].start()].strip()
            if preamble:
                sections.append(
                    {
                        "section": "前文",
                        "content": preamble,
                        "start": 0,
                        "end": matches[0].start(),
                    }
                )

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            section_text = text[start:end].strip()
            section_name = match.group(1)

            if section_text:
                sections.append(
                    {
                        "section": section_name,
                        "content": section_text,
                        "start": start,
                        "end": end,
                    }
                )

        return sections

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        # Approximate: 4 chars per token
        return len(text) // 4

    def _chunk_by_tokens(self, text: str) -> list[str]:
        """Chunk by token count."""
        assert self.tokenizer is not None
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
        Chunk text by sections (legacy API, kept for compatibility).

        Args:
            text: Text to chunk
            section_pattern: Regex pattern to identify section starts

        Returns:
            List of dicts with section info and content
        """
        if not section_pattern:
            section_pattern = r"(第[一二三四五六七八九十百千]+条|第\d+条)"

        return self._split_by_pattern(text, section_pattern)


# Singleton instance
chunking_service = ChunkingService()
