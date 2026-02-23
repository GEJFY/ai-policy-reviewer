"""Pydantic schemas for DocumentGroup."""

from datetime import datetime
from pydantic import BaseModel, Field


class DocumentGroupCreate(BaseModel):
    """Schema for creating a document group."""

    name: str = Field(..., min_length=1, max_length=255, description="グループ名")
    description: str | None = Field(default=None, description="グループ説明")
    document_ids: list[int] = Field(
        default_factory=list, description="初期メンバー文書ID配列"
    )


class DocumentGroupUpdate(BaseModel):
    """Schema for updating a document group."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class DocumentGroupMemberInfo(BaseModel):
    """Schema for document group member info."""

    document_id: int
    document_title: str
    added_at: datetime

    class Config:
        from_attributes = True


class DocumentGroupResponse(BaseModel):
    """Schema for document group response."""

    id: int
    name: str
    description: str | None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class DocumentGroupDetailResponse(DocumentGroupResponse):
    """Schema for detailed document group response."""

    members: list[DocumentGroupMemberInfo] = []


class ConsistencyFinding(BaseModel):
    """Schema for a single consistency finding."""

    document_a_title: str
    document_b_title: str
    location_a: str | None = None
    location_b: str | None = None
    text_a: str | None = None
    text_b: str | None = None
    issue_type: str
    severity: str
    description: str
    suggestion: str | None = None


class ConsistencyCheckResponse(BaseModel):
    """Schema for consistency check result."""

    group_id: int
    group_name: str
    total_findings: int
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    findings: list[ConsistencyFinding] = []


class ConsistencyCheckJobResponse(BaseModel):
    """Schema for async consistency check job."""

    job_id: int
    group_id: int
    status: str
    total_pairs: int = 0
    completed_pairs: int = 0
    progress_percent: float = 0.0

    class Config:
        from_attributes = True
