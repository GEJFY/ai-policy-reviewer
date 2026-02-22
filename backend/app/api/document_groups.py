"""API endpoints for DocumentGroup management."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.document import Document
from app.models.document_group import DocumentGroup, DocumentGroupMember
from app.schemas.document_group import (
    DocumentGroupCreate,
    DocumentGroupUpdate,
    DocumentGroupResponse,
    DocumentGroupDetailResponse,
    DocumentGroupMemberInfo,
    ConsistencyCheckResponse,
    ConsistencyFinding,
)
from app.services.llm_service import llm_service

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

    # Check if already a member
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
    response_model=ConsistencyCheckResponse,
)
async def run_consistency_check(group_id: int, db: Session = Depends(get_db)):
    """Run consistency check on all documents in the group."""
    from app.services.consistency_check_service import check_consistency

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

    document_ids = [m.document_id for m in group.members]
    raw_findings = await check_consistency(db, document_ids)

    high = sum(1 for f in raw_findings if f.get("severity") == "HIGH")
    medium = sum(1 for f in raw_findings if f.get("severity") == "MEDIUM")
    low = sum(1 for f in raw_findings if f.get("severity") == "LOW")

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
        group_id=group.id,
        group_name=group.name,
        total_findings=len(findings),
        high_count=high,
        medium_count=medium,
        low_count=low,
        findings=findings,
    )
