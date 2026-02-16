"""
Review engine for executing AI-powered document reviews.

AIを使用した規程文書のレビューを実行するエンジン。
マルチクラウドLLMプロバイダー（Azure, AWS Bedrock, GCP Vertex AI）対応。

主要機能:
    - チェック項目に基づくレビュー実行
    - RAGパターンによる関連用語・ルールの取得
    - 複数チャンクの効率的な処理
    - マルチクラウドLLMプロバイダー切り替え

対応モデル:
    - Azure Foundry: GPT-5.2, GPT-5-nano, Claude Sonnet/Opus
    - AWS Bedrock: Claude Sonnet 4.6, Opus
    - GCP Vertex AI: Gemini 3.0 Flash/Pro Preview
"""

import json
import time
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.config import LLMProvider
from app.models.term import Term
from app.models.check_item import CheckItem
from app.models.writing_rule import WritingRule
from app.models.document import Document, DocumentChunk
from app.models.review import Review, ReviewCheckItem, ReviewFinding
from app.services.prompt_builder import prompt_builder
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service, LLMResponse

logger = logging.getLogger(__name__)


class ReviewEngine:
    """Engine for executing document reviews using AI."""

    def __init__(self):
        """Initialize the review engine."""
        self._log_initialization()

    def _log_initialization(self):
        """ログ初期化情報を出力"""
        if llm_service.is_available():
            providers = llm_service.get_available_providers()
            provider_names = [p.value for p in providers]
            logger.info(
                f"ReviewEngine initialized | active_provider={llm_service.active_provider.value} | "
                f"available_providers={', '.join(provider_names)}"
            )
        else:
            logger.warning("ReviewEngine not configured - no LLM providers available")

    def is_available(self) -> bool:
        """Check if review engine is available."""
        return llm_service.is_available()

    def get_available_providers(self) -> list[LLMProvider]:
        """利用可能なLLMプロバイダーを返す"""
        return llm_service.get_available_providers()

    def set_provider(self, provider: LLMProvider) -> bool:
        """LLMプロバイダーを切り替え"""
        return llm_service.set_provider(provider)

    async def execute_review(
        self,
        db: Session,
        review_id: int,
        check_item_ids: list[int],
    ) -> list[ReviewFinding]:
        """
        Execute a review on a document.

        Args:
            db: Database session
            review_id: Review ID
            check_item_ids: List of check item IDs to apply

        Returns:
            List of generated findings
        """
        start_time = time.time()

        if not llm_service.is_available():
            logger.error("Review engine not configured - no LLM provider available")
            raise RuntimeError(
                "Review engine not configured - no LLM provider available"
            )

        # Get review and document
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            logger.error(f"Review not found | review_id={review_id}")
            raise ValueError(f"Review {review_id} not found")

        document = db.query(Document).filter(Document.id == review.document_id).first()
        if not document:
            logger.error(f"Document not found | document_id={review.document_id}")
            raise ValueError(f"Document {review.document_id} not found")

        logger.info(
            f"Review started | review_id={review_id} | document_id={document.id} | "
            f"document_title={document.title} | check_items={len(check_item_ids)}"
        )

        # Update review status
        review.status = "processing"
        db.commit()

        all_findings = []
        high_count = 0
        medium_count = 0
        low_count = 0

        try:
            # Get document chunks
            chunks = self._get_document_chunks(db, document.id)
            if not chunks:
                # If no chunks, use extracted text directly
                if document.extracted_text:
                    chunks = [document.extracted_text]
                else:
                    logger.error(f"Document has no content | document_id={document.id}")
                    raise ValueError("Document has no content")

            logger.debug(
                f"Processing document | chunks={len(chunks)} | total_chars={sum(len(c) for c in chunks)}"
            )

            # Process each check item
            for idx, check_item_id in enumerate(check_item_ids):
                # Update check item status
                review_check = (
                    db.query(ReviewCheckItem)
                    .filter(
                        ReviewCheckItem.review_id == review_id,
                        ReviewCheckItem.check_item_id == check_item_id,
                    )
                    .first()
                )
                if review_check:
                    review_check.status = "processing"
                    db.commit()

                check_start = time.time()
                logger.debug(
                    f"Processing check item | check_item_id={check_item_id} | progress={idx + 1}/{len(check_item_ids)}"
                )

                try:
                    # Execute review for this check item
                    findings = await self._execute_check_item(
                        db=db,
                        review_id=review_id,
                        check_item_id=check_item_id,
                        document_chunks=chunks,
                    )
                    all_findings.extend(findings)

                    # Count by severity
                    for f in findings:
                        if f.severity == "HIGH":
                            high_count += 1
                        elif f.severity == "MEDIUM":
                            medium_count += 1
                        else:
                            low_count += 1

                    check_duration = (time.time() - check_start) * 1000
                    logger.info(
                        f"Check item completed | check_item_id={check_item_id} | "
                        f"findings={len(findings)} | duration_ms={check_duration:.2f}"
                    )

                    # Update check item status
                    if review_check:
                        review_check.status = "completed"
                        db.commit()

                except Exception as e:
                    logger.error(
                        f"Check item failed | check_item_id={check_item_id} | error={str(e)}",
                        exc_info=True,
                    )
                    if review_check:
                        review_check.status = "failed"
                        db.commit()

            # Update review status
            review.status = "completed"
            review.completed_at = datetime.now(timezone.utc)
            db.commit()

            duration_sec = time.time() - start_time
            logger.info(
                f"Review completed | review_id={review_id} | "
                f"total_findings={len(all_findings)} | "
                f"high={high_count} | medium={medium_count} | low={low_count} | "
                f"duration_sec={duration_sec:.2f}"
            )

        except Exception as e:
            review.status = "failed"
            db.commit()
            logger.error(
                f"Review failed | review_id={review_id} | error={str(e)}", exc_info=True
            )
            raise e

        return all_findings

    async def _execute_check_item(
        self,
        db: Session,
        review_id: int,
        check_item_id: int,
        document_chunks: list[str],
    ) -> list[ReviewFinding]:
        """Execute a single check item review."""
        # Get check item
        check_item = db.query(CheckItem).filter(CheckItem.id == check_item_id).first()
        if not check_item:
            raise ValueError(f"Check item {check_item_id} not found")

        logger.debug(
            f"Executing check | name={check_item.name} | category={check_item.category}"
        )

        # Get relevant terms using vector search
        terms = await self._get_relevant_terms(db, check_item.name)
        logger.debug(f"Retrieved relevant terms | count={len(terms)}")

        # Get writing rules for this category
        writing_rules = self._get_writing_rules(db, check_item.category)
        logger.debug(f"Retrieved writing rules | count={len(writing_rules)}")

        # Build prompt
        messages = prompt_builder.build_prompt(
            check_item=check_item,
            document_chunks=document_chunks,
            terms=terms,
            writing_rules=writing_rules,
        )

        # Call LLM with retry logic
        response = await self._call_llm_with_retry(messages)

        # Parse response (LLMResponseから直接contentを取得)
        response_text = response.content
        findings = self._parse_findings(
            response_text=response_text,
            review_id=review_id,
            check_item_id=check_item_id,
        )

        # Save findings to database
        db_findings = []
        for finding_data in findings:
            db_finding = ReviewFinding(
                review_id=review_id,
                check_item_id=check_item_id,
                location=finding_data.get("location"),
                original_text=finding_data.get("original_text"),
                issue_type=finding_data.get("issue_type", check_item.category),
                severity=finding_data.get("severity", "MEDIUM"),
                description=finding_data.get("description", ""),
                suggestion=finding_data.get("suggestion"),
                rationale=finding_data.get("rationale"),
                confidence=finding_data.get("confidence"),
                status="PENDING",
            )
            db.add(db_finding)
            db_findings.append(db_finding)

        db.commit()

        # Refresh to get IDs
        for f in db_findings:
            db.refresh(f)

        return db_findings

    async def _call_llm_with_retry(self, messages: list[dict]) -> LLMResponse:
        """
        統合LLMサービスを使用してLLMを呼び出す。

        リトライロジックはllm_service内で処理される。

        Args:
            messages: LLMに送信するメッセージリスト

        Returns:
            LLMResponse: 統合されたレスポンスオブジェクト
        """
        llm_start = time.time()

        response = await llm_service.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=4000,
            json_mode=True,
        )

        llm_duration = (time.time() - llm_start) * 1000
        logger.debug(
            f"LLM call completed | provider={response.provider} | "
            f"model={response.model} | duration_ms={llm_duration:.2f} | "
            f"prompt_tokens={response.usage.get('prompt_tokens', 0)} | "
            f"completion_tokens={response.usage.get('completion_tokens', 0)} | "
            f"total_tokens={response.usage.get('total_tokens', 0)}"
        )

        return response

    def _get_document_chunks(self, db: Session, document_id: int) -> list[str]:
        """Get document chunks from database."""
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )
        return [chunk.content for chunk in chunks]

    async def _get_relevant_terms(
        self, db: Session, query: str, top_k: int = 10
    ) -> list[Term]:
        """Get relevant terms using vector search."""
        if not embedding_service.is_available():
            logger.debug("Embedding service not available, using fallback")
            return db.query(Term).limit(top_k).all()

        try:
            query_embedding = await embedding_service.get_embedding(query)
            results = vector_store.search_similar_terms(
                db=db, query_embedding=query_embedding, top_k=top_k
            )
            return [term for term, score in results]
        except Exception as e:
            logger.warning(f"Vector search failed, using fallback | error={str(e)}")
            return db.query(Term).limit(top_k).all()

    def _get_writing_rules(self, db: Session, category: str) -> list[WritingRule]:
        """Get writing rules for a category."""
        return (
            db.query(WritingRule)
            .filter(WritingRule.is_active.is_(True))
            .limit(20)
            .all()
        )

    def _parse_findings(
        self,
        response_text: str,
        review_id: int,
        check_item_id: int,
    ) -> list[dict]:
        """Parse LLM response into findings."""
        try:
            data = json.loads(response_text)
            findings = data.get("findings", [])

            # Validate and normalize findings
            normalized = []
            skipped = 0
            for f in findings:
                if not isinstance(f, dict):
                    skipped += 1
                    continue
                if not f.get("description"):
                    skipped += 1
                    continue

                # confidenceをLLM出力から取得、なければseverityから推定
                raw_confidence = f.get("confidence")
                if raw_confidence is not None:
                    try:
                        confidence = min(1.0, max(0.0, float(raw_confidence)))
                    except (ValueError, TypeError):
                        confidence = None
                else:
                    # severityベースのデフォルト信頼度
                    severity_val = f.get("severity", "MEDIUM").upper()
                    confidence = {"HIGH": 0.9, "MEDIUM": 0.7, "LOW": 0.5}.get(
                        severity_val, 0.7
                    )

                normalized.append(
                    {
                        "location": f.get("location", ""),
                        "original_text": f.get("original_text", ""),
                        "issue_type": f.get("issue_type", ""),
                        "severity": f.get("severity", "MEDIUM").upper(),
                        "description": f.get("description", ""),
                        "suggestion": f.get("suggestion"),
                        "rationale": f.get("rationale"),
                        "confidence": confidence,
                    }
                )

            if skipped > 0:
                logger.debug(f"Skipped invalid findings | count={skipped}")

            logger.debug(
                f"Parsed findings | total={len(findings)} | valid={len(normalized)}"
            )
            return normalized

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse LLM response | error={str(e)} | "
                f"response_preview={response_text[:200]}"
            )
            # Try to extract any useful information
            return [
                {
                    "location": "",
                    "original_text": "",
                    "issue_type": "PARSE_ERROR",
                    "severity": "LOW",
                    "description": f"レビュー結果の解析に失敗しました: {str(e)[:100]}",
                    "suggestion": None,
                    "rationale": response_text[:500],
                }
            ]


# Singleton instance
review_engine = ReviewEngine()
