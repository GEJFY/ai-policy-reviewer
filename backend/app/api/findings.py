"""API endpoints for ReviewFinding management."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.review import Review, ReviewFinding
from app.schemas.finding import (
    FindingResponse,
    FindingApprovalRequest,
    BulkApprovalRequest,
    FindingSummary,
)


router = APIRouter(prefix="/api/v1", tags=["Findings"])


@router.get("/reviews/{review_id}/findings", response_model=list[FindingResponse])
async def list_review_findings(
    review_id: int,
    severity: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get findings for a specific review."""
    # Verify review exists
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    query = db.query(ReviewFinding).filter(ReviewFinding.review_id == review_id)

    if severity:
        query = query.filter(ReviewFinding.severity == severity.upper())

    if status:
        query = query.filter(ReviewFinding.status == status.upper())

    return query.order_by(ReviewFinding.severity.desc(), ReviewFinding.created_at).all()


@router.get("/reviews/{review_id}/findings/summary", response_model=FindingSummary)
async def get_findings_summary(review_id: int, db: Session = Depends(get_db)):
    """Get summary statistics for review findings."""
    # Verify review exists
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    findings = db.query(ReviewFinding).filter(ReviewFinding.review_id == review_id).all()

    return FindingSummary(
        total_findings=len(findings),
        high_count=sum(1 for f in findings if f.severity == "HIGH"),
        medium_count=sum(1 for f in findings if f.severity == "MEDIUM"),
        low_count=sum(1 for f in findings if f.severity == "LOW"),
        pending_count=sum(1 for f in findings if f.status == "PENDING"),
        approved_count=sum(1 for f in findings if f.status == "APPROVED"),
        rejected_count=sum(1 for f in findings if f.status == "REJECTED"),
        deferred_count=sum(1 for f in findings if f.status == "DEFERRED"),
    )


@router.get("/findings/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: int, db: Session = Depends(get_db)):
    """Get a specific finding by ID."""
    finding = db.query(ReviewFinding).filter(ReviewFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.put("/findings/{finding_id}/approve", response_model=FindingResponse)
async def approve_finding(
    finding_id: int,
    request: FindingApprovalRequest,
    db: Session = Depends(get_db),
):
    """Approve a finding."""
    finding = db.query(ReviewFinding).filter(ReviewFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.status = "APPROVED"
    finding.reviewed_at = datetime.now(timezone.utc)
    finding.comment = request.comment

    db.commit()
    db.refresh(finding)

    return finding


@router.put("/findings/{finding_id}/reject", response_model=FindingResponse)
async def reject_finding(
    finding_id: int,
    request: FindingApprovalRequest,
    db: Session = Depends(get_db),
):
    """Reject a finding."""
    finding = db.query(ReviewFinding).filter(ReviewFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.status = "REJECTED"
    finding.reviewed_at = datetime.now(timezone.utc)
    finding.comment = request.comment

    db.commit()
    db.refresh(finding)

    return finding


@router.put("/findings/{finding_id}/defer", response_model=FindingResponse)
async def defer_finding(
    finding_id: int,
    request: FindingApprovalRequest,
    db: Session = Depends(get_db),
):
    """Defer a finding for later review."""
    finding = db.query(ReviewFinding).filter(ReviewFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.status = "DEFERRED"
    finding.reviewed_at = datetime.now(timezone.utc)
    finding.comment = request.comment

    db.commit()
    db.refresh(finding)

    return finding


@router.post("/reviews/{review_id}/findings/bulk-approve", response_model=list[FindingResponse])
async def bulk_approve_findings(
    review_id: int,
    request: BulkApprovalRequest,
    db: Session = Depends(get_db),
):
    """Bulk approve/reject/defer findings."""
    # Verify review exists
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Get findings
    findings = (
        db.query(ReviewFinding)
        .filter(
            ReviewFinding.review_id == review_id,
            ReviewFinding.id.in_(request.finding_ids),
        )
        .all()
    )

    if len(findings) != len(request.finding_ids):
        raise HTTPException(
            status_code=400,
            detail="Some finding IDs are invalid or don't belong to this review",
        )

    # Update findings
    now = datetime.now(timezone.utc)
    for finding in findings:
        finding.status = request.action.value
        finding.reviewed_at = now
        finding.comment = request.comment

    db.commit()

    # Refresh and return
    for f in findings:
        db.refresh(f)

    return findings


@router.put("/findings/{finding_id}/reset", response_model=FindingResponse)
async def reset_finding(finding_id: int, db: Session = Depends(get_db)):
    """Reset a finding status to pending."""
    finding = db.query(ReviewFinding).filter(ReviewFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.status = "PENDING"
    finding.reviewed_at = None
    finding.reviewed_by = None
    finding.comment = None

    db.commit()
    db.refresh(finding)

    return finding
