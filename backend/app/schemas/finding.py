"""Pydantic schemas for ReviewFinding."""

from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class FindingStatus(str, Enum):
    """Finding approval status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"


class Severity(str, Enum):
    """Severity level."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FindingBase(BaseModel):
    """Base schema for Finding."""
    location: str | None = Field(default=None, description="該当箇所（条項番号・行番号）")
    original_text: str | None = Field(default=None, description="問題のある原文")
    issue_type: str = Field(..., description="問題種別")
    severity: str = Field(..., description="重要度")
    description: str = Field(..., description="問題の説明")
    suggestion: str | None = Field(default=None, description="改善提案")
    rationale: str | None = Field(default=None, description="指摘根拠")


class FindingResponse(FindingBase):
    """Schema for finding response."""
    id: int
    review_id: int
    check_item_id: int | None
    status: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class FindingApprovalRequest(BaseModel):
    """Schema for approving/rejecting a finding."""
    comment: str | None = Field(default=None, description="レビューコメント")


class BulkApprovalRequest(BaseModel):
    """Schema for bulk approval."""
    finding_ids: list[int] = Field(..., min_length=1, description="対象指摘事項ID配列")
    action: FindingStatus = Field(..., description="アクション（APPROVE/REJECT/DEFER）")
    comment: str | None = Field(default=None, description="コメント")


class FindingSummary(BaseModel):
    """Schema for finding summary statistics."""
    total_findings: int
    high_count: int
    medium_count: int
    low_count: int
    pending_count: int
    approved_count: int
    rejected_count: int
    deferred_count: int
