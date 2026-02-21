"""API endpoint for dashboard statistics."""

from fastapi import APIRouter, Depends
from sqlalchemy import case, func as sa_func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.document import Document
from app.models.review import Review, ReviewFinding
from app.models.term import Term
from app.models.check_item import CheckItem
from app.models.writing_rule import WritingRule

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


class SeverityCounts(BaseModel):
    """重要度別の指摘件数"""

    high: int = 0
    medium: int = 0
    low: int = 0


class StatusCounts(BaseModel):
    """ステータス別の件数"""

    pending: int = 0
    approved: int = 0
    rejected: int = 0
    deferred: int = 0


class ReviewStatusCounts(BaseModel):
    """レビューステータス別の件数"""

    pending: int = 0
    processing: int = 0
    completed: int = 0
    failed: int = 0


class DashboardStats(BaseModel):
    """ダッシュボード統計情報"""

    document_count: int
    review_count: int
    term_count: int
    check_item_count: int
    writing_rule_count: int
    finding_total: int
    finding_by_severity: SeverityCounts
    finding_by_status: StatusCounts
    review_by_status: ReviewStatusCounts


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    ダッシュボードの統計情報を1エンドポイントで取得する。

    フロントエンドのダッシュボードページで使用。
    個別APIを複数呼び出す代わりに、集計済みデータを一括返却する。
    """
    # マスタデータの件数（軽量COUNT）
    document_count = db.query(sa_func.count(Document.id)).scalar() or 0
    review_count = db.query(sa_func.count(Review.id)).scalar() or 0
    term_count = db.query(sa_func.count(Term.id)).scalar() or 0
    check_item_count = db.query(sa_func.count(CheckItem.id)).scalar() or 0
    writing_rule_count = db.query(sa_func.count(WritingRule.id)).scalar() or 0

    # Finding集計（severity別 + status別を1クエリで取得）
    finding_agg = db.query(
        sa_func.count(ReviewFinding.id).label("total"),
        sa_func.sum(case((ReviewFinding.severity == "HIGH", 1), else_=0)).label("high"),
        sa_func.sum(case((ReviewFinding.severity == "MEDIUM", 1), else_=0)).label(
            "medium"
        ),
        sa_func.sum(case((ReviewFinding.severity == "LOW", 1), else_=0)).label("low"),
        sa_func.sum(case((ReviewFinding.status == "PENDING", 1), else_=0)).label(
            "pending"
        ),
        sa_func.sum(case((ReviewFinding.status == "APPROVED", 1), else_=0)).label(
            "approved"
        ),
        sa_func.sum(case((ReviewFinding.status == "REJECTED", 1), else_=0)).label(
            "rejected"
        ),
        sa_func.sum(case((ReviewFinding.status == "DEFERRED", 1), else_=0)).label(
            "deferred"
        ),
    ).first()

    # Review status集計
    review_status_agg = db.query(
        sa_func.sum(case((Review.status == "pending", 1), else_=0)).label("pending"),
        sa_func.sum(case((Review.status == "processing", 1), else_=0)).label(
            "processing"
        ),
        sa_func.sum(case((Review.status == "completed", 1), else_=0)).label(
            "completed"
        ),
        sa_func.sum(case((Review.status == "failed", 1), else_=0)).label("failed"),
    ).first()

    return DashboardStats(
        document_count=document_count,
        review_count=review_count,
        term_count=term_count,
        check_item_count=check_item_count,
        writing_rule_count=writing_rule_count,
        finding_total=finding_agg.total if finding_agg else 0,
        finding_by_severity=SeverityCounts(
            high=int(finding_agg.high or 0) if finding_agg else 0,
            medium=int(finding_agg.medium or 0) if finding_agg else 0,
            low=int(finding_agg.low or 0) if finding_agg else 0,
        ),
        finding_by_status=StatusCounts(
            pending=int(finding_agg.pending or 0) if finding_agg else 0,
            approved=int(finding_agg.approved or 0) if finding_agg else 0,
            rejected=int(finding_agg.rejected or 0) if finding_agg else 0,
            deferred=int(finding_agg.deferred or 0) if finding_agg else 0,
        ),
        review_by_status=ReviewStatusCounts(
            pending=int(review_status_agg.pending or 0) if review_status_agg else 0,
            processing=(
                int(review_status_agg.processing or 0) if review_status_agg else 0
            ),
            completed=int(review_status_agg.completed or 0) if review_status_agg else 0,
            failed=int(review_status_agg.failed or 0) if review_status_agg else 0,
        ),
    )
