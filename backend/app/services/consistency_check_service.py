"""Consistency check service for cross-document analysis."""

import json
import logging
from typing import Callable, Optional

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

CONSISTENCY_PROMPT = """# 規程間整合性チェック

## 目的
2つの社内規程文書間の整合性を分析し、矛盾・不一致・重複を検出します。

## 文書A: {doc_a_title}
{doc_a_content}

## 文書B: {doc_b_title}
{doc_b_content}

## チェック観点

1. **定義の不一致**: 同一用語が異なる定義で使用されていないか
2. **条件の矛盾**: 一方で認められていることが他方で禁止されていないか
3. **参照の不整合**: 相互参照が正しいか、参照先が存在するか
4. **範囲の重複**: 同一事項について異なるルールが定められていないか
5. **責任主体の不一致**: 同一業務の責任者が文書間で異なっていないか

## 出力形式
必ず以下のJSON形式で出力してください（マークダウンコードブロック不可）:
{{
  "findings": [
    {{
      "location_a": "文書Aの該当箇所（条項番号等）",
      "location_b": "文書Bの該当箇所（条項番号等）",
      "text_a": "文書Aの該当テキスト",
      "text_b": "文書Bの該当テキスト",
      "issue_type": "DEFINITION_MISMATCH|CONTRADICTION|REFERENCE_ERROR|OVERLAP|RESPONSIBILITY_MISMATCH",
      "severity": "HIGH|MEDIUM|LOW",
      "description": "不整合の説明",
      "suggestion": "改善提案"
    }}
  ],
  "summary": {{"total_findings": 0, "high_count": 0, "medium_count": 0, "low_count": 0}}
}}

指摘がない場合は空の findings 配列を返してください。
"""


async def check_consistency(
    db: Session,
    document_ids: list[int],
) -> list[dict]:
    """Check consistency between multiple documents."""
    return await check_consistency_with_progress(db, document_ids)


async def check_consistency_with_progress(
    db: Session,
    document_ids: list[int],
    on_pair_complete: Optional[Callable[[int], None]] = None,
) -> list[dict]:
    """Check consistency between multiple documents with progress callback.

    For each pair of documents, uses vector search to find similar chunks,
    then sends them to LLM for consistency analysis.

    Args:
        db: Database session
        document_ids: List of document IDs to check
        on_pair_complete: Optional callback called with the number of completed pairs

    Returns:
        List of consistency findings
    """
    if not llm_service.is_available():
        raise RuntimeError("LLM service not available")

    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
    doc_map: dict[int, Document] = {int(d.id): d for d in documents}

    all_findings = []
    completed = 0

    # Check each pair of documents
    for i in range(len(document_ids)):
        for j in range(i + 1, len(document_ids)):
            doc_a = doc_map.get(document_ids[i])
            doc_b = doc_map.get(document_ids[j])
            if not doc_a or not doc_b:
                completed += 1
                if on_pair_complete:
                    on_pair_complete(completed)
                continue

            findings = await _check_pair(db, doc_a, doc_b)
            all_findings.extend(findings)

            completed += 1
            if on_pair_complete:
                on_pair_complete(completed)

    return all_findings


async def _check_pair(
    db: Session,
    doc_a: Document,
    doc_b: Document,
) -> list[dict]:
    """Check consistency between a pair of documents."""
    # Get content - use chunks or extracted text
    content_a = _get_document_content(db, doc_a)
    content_b = _get_document_content(db, doc_b)

    if not content_a or not content_b:
        logger.warning(
            f"Skipping pair: doc_a={doc_a.id} doc_b={doc_b.id} - missing content"
        )
        return []

    # Truncate to reasonable size for LLM
    max_chars = 8000
    content_a = content_a[:max_chars]
    content_b = content_b[:max_chars]

    prompt = CONSISTENCY_PROMPT.format(
        doc_a_title=doc_a.title,
        doc_b_title=doc_b.title,
        doc_a_content=content_a,
        doc_b_content=content_b,
    )

    try:
        response = await llm_service.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4000,
            json_mode=True,
        )
        if not response or not response.content:
            return []

        parsed = _parse_response(response.content)
        # Attach document titles
        for f in parsed:
            f["document_a_title"] = doc_a.title
            f["document_b_title"] = doc_b.title

        return parsed
    except Exception as e:
        logger.error(
            f"Consistency check failed for pair: "
            f"doc_a={doc_a.id} doc_b={doc_b.id} error={e}"
        )
        return []


def _get_document_content(db: Session, doc: Document) -> str:
    """Get document content from chunks or extracted text."""
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc.id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )
    if chunks:
        return "\n".join(str(c.content) for c in chunks)
    return str(doc.extracted_text or "")


def _parse_response(content: str) -> list[dict]:
    """Parse LLM response JSON."""
    try:
        # Try direct parse
        data = json.loads(content)
        return data.get("findings", [])
    except json.JSONDecodeError:
        # Try to extract JSON from text
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(content[start:end])
                return data.get("findings", [])
            except json.JSONDecodeError:
                pass
    logger.warning("Failed to parse consistency check response")
    return []
