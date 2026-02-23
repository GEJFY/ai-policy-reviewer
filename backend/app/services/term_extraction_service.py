"""Service for extracting term candidates from reviewed documents using LLM."""

import json
import logging
from sqlalchemy.orm import Session

from app.models.term import Term, TermCandidate
from app.models.document import Document, DocumentChunk
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
あなたは規程文書の用語抽出の専門家です。
以下の文書テキストから、社内用語辞書に登録すべき重要な専門用語・略語・固有名詞を抽出してください。

## 抽出ルール
- 5〜15個程度を目安に抽出
- 一般的な日本語ではなく、組織固有の用語や業界専門用語を優先
- 既に登録済みの用語は除外すること
- 各用語について定義案、カテゴリ、文書内の使用箇所を提示

## 既存の登録済み用語（除外対象）
{existing_terms}

## 文書テキスト
{document_text}

## 出力形式（JSON）
{{
  "candidates": [
    {{
      "term": "用語名",
      "definition": "この用語の定義案",
      "category": "人事/財務/IT/法務/一般 のいずれか",
      "context": "文書内での使用箇所の引用（50文字程度）",
      "confidence": 0.8
    }}
  ]
}}

JSONのみ出力してください。
"""


class TermExtractionService:
    """Service for extracting term candidates from document text."""

    async def extract_candidates(
        self,
        db: Session,
        review_id: int,
        document_id: int,
    ) -> list[TermCandidate]:
        """Extract term candidates from a document after review.

        Args:
            db: Database session
            review_id: Review ID that triggered extraction
            document_id: Document to extract terms from

        Returns:
            List of created TermCandidate records
        """
        if not llm_service.is_available():
            logger.warning("LLM not available, skipping term extraction")
            return []

        # Get document text
        document_text = self._get_document_text(db, document_id)
        if not document_text:
            logger.warning(
                f"No document text for extraction | document_id={document_id}"
            )
            return []

        # Truncate if too long (keep first ~8000 chars for prompt)
        if len(document_text) > 8000:
            document_text = document_text[:8000] + "\n...(以下省略)"

        # Get existing terms to exclude
        existing_terms = db.query(Term.term).all()
        existing_list = (
            ", ".join(t.term for t in existing_terms) if existing_terms else "（なし）"
        )

        # Also exclude already-extracted pending candidates for this document
        existing_candidates = (
            db.query(TermCandidate.term)
            .filter(
                TermCandidate.document_id == document_id,
                TermCandidate.status == "pending",
            )
            .all()
        )
        if existing_candidates:
            existing_list += ", " + ", ".join(c.term for c in existing_candidates)

        # Build prompt
        prompt_text = EXTRACTION_PROMPT.format(
            existing_terms=existing_list,
            document_text=document_text,
        )

        messages = [
            {"role": "system", "content": "あなたは規程文書分析の専門家です。"},
            {"role": "user", "content": prompt_text},
        ]

        try:
            response = await llm_service.generate(
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                json_mode=True,
            )

            candidates = self._parse_response(response.content, review_id, document_id)

            # Save to database
            db_candidates = []
            for data in candidates:
                candidate = TermCandidate(
                    review_id=review_id,
                    document_id=document_id,
                    term=data["term"],
                    definition=data.get("definition"),
                    category=data.get("category"),
                    context=data.get("context"),
                    confidence=data.get("confidence"),
                    status="pending",
                )
                db.add(candidate)
                db_candidates.append(candidate)

            db.commit()
            for c in db_candidates:
                db.refresh(c)

            logger.info(
                f"Term extraction completed | review_id={review_id} | "
                f"document_id={document_id} | candidates={len(db_candidates)}"
            )
            return db_candidates

        except Exception as e:
            logger.error(
                f"Term extraction failed | review_id={review_id} | "
                f"document_id={document_id} | error={str(e)}",
                exc_info=True,
            )
            return []

    def _get_document_text(self, db: Session, document_id: int) -> str:
        """Get full document text from chunks or extracted_text."""
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )
        if chunks:
            return "\n".join(c.content for c in chunks)

        document = db.query(Document).filter(Document.id == document_id).first()
        if document and document.extracted_text:
            return document.extracted_text

        return ""

    def _parse_response(
        self, response_text: str, review_id: int, document_id: int
    ) -> list[dict]:
        """Parse LLM response into candidate dicts."""
        try:
            data = json.loads(response_text)
            raw_candidates = data.get("candidates", [])

            valid = []
            for c in raw_candidates:
                if not isinstance(c, dict):
                    continue
                term = c.get("term", "").strip()
                if not term:
                    continue

                confidence = c.get("confidence")
                if confidence is not None:
                    try:
                        confidence = min(1.0, max(0.0, float(confidence)))
                    except (ValueError, TypeError):
                        confidence = None

                valid.append(
                    {
                        "term": term,
                        "definition": c.get("definition", ""),
                        "category": c.get("category", "一般"),
                        "context": c.get("context", ""),
                        "confidence": confidence,
                    }
                )

            logger.debug(
                f"Parsed term candidates | total={len(raw_candidates)} | valid={len(valid)}"
            )
            return valid

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse term extraction response | error={str(e)} | "
                f"response_preview={response_text[:200]}"
            )
            return []


# Singleton instance
term_extraction_service = TermExtractionService()
