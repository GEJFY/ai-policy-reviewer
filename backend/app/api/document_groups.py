"""API endpoints for DocumentGroup management."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.document import Document
from app.models.document_group import (
    ConsistencyCheckJob,
    DocumentGroup,
    DocumentGroupMember,
)
from app.schemas.document_group import (
    DocumentGroupCreate,
    DocumentGroupUpdate,
    DocumentGroupResponse,
    DocumentGroupDetailResponse,
    DocumentGroupMemberInfo,
    ConsistencyCheckResponse,
    ConsistencyCheckJobResponse,
    ConsistencyFinding,
)
from app.services.llm_service import llm_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/document-groups", tags=["Document Groups"])


@router.get("", response_model=list[DocumentGroupResponse])
async def list_groups(db: Session = Depends(get_db)):
    """List all document groups."""
    groups = db.query(DocumentGroup).order_by(DocumentGroup.created_at.desc()).all()
    result = []
    for g in groups:
        result.append(
            DocumentGroupResponse(
                id=g.id,
                name=g.name,
                description=g.description,
                member_count=len(g.members),
                created_at=g.created_at,
                updated_at=g.updated_at,
            )
        )
    return result


@router.post("", response_model=DocumentGroupDetailResponse, status_code=201)
async def create_group(request: DocumentGroupCreate, db: Session = Depends(get_db)):
    """Create a new document group."""
    group = DocumentGroup(name=request.name, description=request.description)
    db.add(group)
    db.commit()
    db.refresh(group)

    members = []
    for doc_id in request.document_ids:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            continue
        member = DocumentGroupMember(group_id=group.id, document_id=doc_id)
        db.add(member)
        members.append(
            DocumentGroupMemberInfo(
                document_id=doc.id,
                document_title=doc.title,
                added_at=member.added_at or group.created_at,
            )
        )
    db.commit()

    return DocumentGroupDetailResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        member_count=len(members),
        created_at=group.created_at,
        updated_at=group.updated_at,
        members=members,
    )


@router.get("/{group_id}", response_model=DocumentGroupDetailResponse)
async def get_group(group_id: int, db: Session = Depends(get_db)):
    """Get a document group with members."""
    group = db.query(DocumentGroup).filter(DocumentGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Document group not found")

    members = []
    for m in group.members:
        doc = db.query(Document).filter(Document.id == m.document_id).first()
        if doc:
            members.append(
                DocumentGroupMemberInfo(
                    document_id=doc.id,
                    document_title=doc.title,
                    added_at=m.added_at,
                )
            )

    return DocumentGroupDetailResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        member_count=len(members),
        created_at=group.created_at,
        updated_at=group.updated_at,
        members=members,
    )


@router.put("/{group_id}", response_model=DocumentGroupResponse)
async def update_group(
    group_id: int,
    request: DocumentGroupUpdate,
    db: Session = Depends(get_db),
):
    """Update a document group."""
    group = db.query(DocumentGroup).filter(DocumentGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Document group not found")

    if request.name is not None:
        group.name = request.name
    if request.description is not None:
        group.description = request.description
    db.commit()
    db.refresh(group)

    return DocumentGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        member_count=len(group.members),
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.delete("/{group_id}", status_code=204)
async def delete_group(group_id: int, db: Session = Depends(get_db)):
    """Delete a document group."""
    group = db.query(DocumentGroup).filter(DocumentGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Document group not found")
    db.delete(group)
    db.commit()
    return None


@router.post("/{group_id}/members", status_code=201)
async def add_member(group_id: int, document_id: int, db: Session = Depends(get_db)):
    """Add a document to a group."""
    group = db.query(DocumentGroup).filter(DocumentGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Document group not found")

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    existing = (
        db.query(DocumentGroupMember)
        .filter(
            DocumentGroupMember.group_id == group_id,
            DocumentGroupMember.document_id == document_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Document already in group")

    member = DocumentGroupMember(group_id=group_id, document_id=document_id)
    db.add(member)
    db.commit()
    return {"message": "Document added to group"}


@router.delete("/{group_id}/members/{document_id}", status_code=204)
async def remove_member(group_id: int, document_id: int, db: Session = Depends(get_db)):
    """Remove a document from a group."""
    member = (
        db.query(DocumentGroupMember)
        .filter(
            DocumentGroupMember.group_id == group_id,
            DocumentGroupMember.document_id == document_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return None


@router.post(
    "/{group_id}/consistency-check",
    response_model=ConsistencyCheckJobResponse,
    status_code=202,
)
async def run_consistency_check(
    group_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start async consistency check on all documents in the group."""
    group = db.query(DocumentGroup).filter(DocumentGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Document group not found")

    if len(group.members) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 documents are required for consistency check",
        )

    if not llm_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="LLM service not available. Check provider configuration.",
        )

    # Calculate total pairs: n*(n-1)/2
    n = len(group.members)
    total_pairs = n * (n - 1) // 2

    job = ConsistencyCheckJob(
        group_id=group_id,
        status="processing",
        total_pairs=total_pairs,
        completed_pairs=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    document_ids = [m.document_id for m in group.members]

    background_tasks.add_task(
        execute_consistency_check_task,
        job.id,
        group_id,
        document_ids,
    )

    return ConsistencyCheckJobResponse(
        job_id=job.id,
        group_id=group_id,
        status="processing",
        total_pairs=total_pairs,
        completed_pairs=0,
        progress_percent=0.0,
    )


@router.get("/{group_id}/consistency-check/{job_id}")
async def get_consistency_check_status(
    group_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get the status/result of a consistency check job."""
    job = (
        db.query(ConsistencyCheckJob)
        .filter(
            ConsistencyCheckJob.id == job_id,
            ConsistencyCheckJob.group_id == group_id,
        )
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Consistency check job not found")

    if job.status == "completed" and job.result_json:
        raw_findings = json.loads(str(job.result_json))
        high = sum(1 for f in raw_findings if f.get("severity") == "HIGH")
        medium = sum(1 for f in raw_findings if f.get("severity") == "MEDIUM")
        low = sum(1 for f in raw_findings if f.get("severity") == "LOW")

        group = db.query(DocumentGroup).filter(DocumentGroup.id == group_id).first()
        group_name = group.name if group else ""

        findings = [
            ConsistencyFinding(
                document_a_title=f.get("document_a_title", ""),
                document_b_title=f.get("document_b_title", ""),
                location_a=f.get("location_a"),
                location_b=f.get("location_b"),
                text_a=f.get("text_a"),
                text_b=f.get("text_b"),
                issue_type=f.get("issue_type", "UNKNOWN"),
                severity=f.get("severity", "LOW"),
                description=f.get("description", ""),
                suggestion=f.get("suggestion"),
            )
            for f in raw_findings
        ]

        return ConsistencyCheckResponse(
            group_id=group_id,
            group_name=group_name,
            total_findings=len(findings),
            high_count=high,
            medium_count=medium,
            low_count=low,
            findings=findings,
        )

    # Return progress
    progress = 0.0
    if job.total_pairs and job.total_pairs > 0:
        progress = float((job.completed_pairs or 0)) / float(job.total_pairs) * 100

    error_detail = None
    if job.status == "failed":
        error_detail = job.error_message

    return {
        "job_id": job.id,
        "group_id": group_id,
        "status": job.status,
        "total_pairs": job.total_pairs or 0,
        "completed_pairs": job.completed_pairs or 0,
        "progress_percent": round(progress, 1),
        "error": error_detail,
    }


async def execute_consistency_check_task(
    job_id: int,
    group_id: int,
    document_ids: list[int],
):
    """Background task for consistency check execution."""
    from app.db.database import SessionLocal
    from app.services.consistency_check_service import check_consistency_with_progress

    logger.info(
        f"Starting consistency check: job_id={job_id}, group_id={group_id}, "
        f"documents={document_ids}"
    )

    db = SessionLocal()
    try:

        def on_pair_complete(completed: int):
            job = (
                db.query(ConsistencyCheckJob)
                .filter(ConsistencyCheckJob.id == job_id)
                .first()
            )
            if job:
                job.completed_pairs = completed
                db.commit()

        all_findings = await check_consistency_with_progress(
            db=db,
            document_ids=document_ids,
            on_pair_complete=on_pair_complete,
        )

        job = (
            db.query(ConsistencyCheckJob)
            .filter(ConsistencyCheckJob.id == job_id)
            .first()
        )
        if job:
            job.status = "completed"
            job.result_json = json.dumps(all_findings, ensure_ascii=False)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

        logger.info(
            f"Consistency check completed: job_id={job_id}, "
            f"findings={len(all_findings)}"
        )
    except Exception as e:
        logger.error(
            f"Consistency check failed: job_id={job_id}, error={e}", exc_info=True
        )
        job = (
            db.query(ConsistencyCheckJob)
            .filter(ConsistencyCheckJob.id == job_id)
            .first()
        )
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()
