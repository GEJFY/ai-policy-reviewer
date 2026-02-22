"""API endpoints for ReviewFinding management."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.document import Document, DocumentChunk
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

    findings = (
        db.query(ReviewFinding).filter(ReviewFinding.review_id == review_id).all()
    )

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
    if request.edited_suggestion is not None:
        finding.edited_suggestion = request.edited_suggestion

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


@router.post(
    "/reviews/{review_id}/findings/bulk-approve", response_model=list[FindingResponse]
)
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
    finding.edited_suggestion = None

    db.commit()
    db.refresh(finding)

    return finding


@router.get("/findings/{finding_id}/context")
async def get_finding_context(finding_id: int, db: Session = Depends(get_db)):
    """Get surrounding context for a finding.

    Returns the chunk text containing the original_text with highlight positions,
    plus a preview of the corrected text.
    """
    finding = db.query(ReviewFinding).filter(ReviewFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    review = db.query(Review).filter(Review.id == finding.review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    document = db.query(Document).filter(Document.id == review.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Find the chunk containing the original text
    context_text = ""
    highlight_start = -1
    highlight_end = -1

    if finding.original_text and document.extracted_text:
        full_text = document.extracted_text
        idx = full_text.find(finding.original_text)
        if idx >= 0:
            # Get surrounding context (up to 200 chars before/after)
            start = max(0, idx - 200)
            end = min(len(full_text), idx + len(finding.original_text) + 200)
            context_text = full_text[start:end]
            highlight_start = idx - start
            highlight_end = highlight_start + len(finding.original_text)
        else:
            # Fallback: search in chunks
            chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == document.id)
                .order_by(DocumentChunk.chunk_index)
                .all()
            )
            for chunk in chunks:
                cidx = chunk.content.find(finding.original_text)
                if cidx >= 0:
                    context_text = chunk.content
                    highlight_start = cidx
                    highlight_end = cidx + len(finding.original_text)
                    break

    # Build corrected preview
    suggestion = finding.edited_suggestion or finding.suggestion
    corrected_text = ""
    if context_text and highlight_start >= 0 and suggestion:
        corrected_text = (
            context_text[:highlight_start] + suggestion + context_text[highlight_end:]
        )

    return {
        "finding_id": finding.id,
        "context_text": context_text,
        "highlight_start": highlight_start,
        "highlight_end": highlight_end,
        "original_text": finding.original_text,
        "suggestion": suggestion,
        "corrected_text": corrected_text,
    }


@router.get("/reviews/{review_id}/revised-text")
async def get_revised_text(review_id: int, db: Session = Depends(get_db)):
    """Get document text with all approved findings applied.

    Returns the full document text with approved suggestions applied.
    Uses edited_suggestion when available, falls back to original suggestion.
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    document = db.query(Document).filter(Document.id == review.document_id).first()
    if not document or not document.extracted_text:
        raise HTTPException(status_code=404, detail="Document text not available")

    # Get approved findings sorted by position (reverse order for safe replacement)
    approved_findings = (
        db.query(ReviewFinding)
        .filter(
            ReviewFinding.review_id == review_id,
            ReviewFinding.status == "APPROVED",
            ReviewFinding.original_text.isnot(None),
        )
        .all()
    )

    revised_text = document.extracted_text
    changes_applied = 0

    # Build replacements list with positions
    replacements = []
    for f in approved_findings:
        suggestion = f.edited_suggestion or f.suggestion
        if not suggestion or not f.original_text:
            continue
        idx = revised_text.find(f.original_text)
        if idx >= 0:
            replacements.append(
                {
                    "start": idx,
                    "end": idx + len(f.original_text),
                    "original": f.original_text,
                    "replacement": suggestion,
                }
            )

    # Sort by position descending to apply from end to start (preserves positions)
    replacements.sort(key=lambda r: r["start"], reverse=True)

    for r in replacements:
        revised_text = (
            revised_text[: r["start"]] + r["replacement"] + revised_text[r["end"] :]
        )
        changes_applied += 1

    return {
        "review_id": review_id,
        "original_text": document.extracted_text,
        "revised_text": revised_text,
        "changes_applied": changes_applied,
        "total_approved": len(approved_findings),
    }
