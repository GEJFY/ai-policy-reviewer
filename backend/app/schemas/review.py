"""Pydantic schemas for Review."""

from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ReviewStatus(str, Enum):
    """Review processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewCreate(BaseModel):
    """Schema for creating a new review."""
    document_id: int = Field(..., description="レビュー対象文書ID")
    check_item_ids: list[int] = Field(..., min_length=1, description="適用するチェック項目ID配列")


class ReviewCheckItemStatus(BaseModel):
    """Schema for review check item status."""
    check_item_id: int
    check_item_name: str
    status: str


class ReviewResponse(BaseModel):
    """Schema for review response."""
    id: int
    document_id: int
    status: str
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class ReviewDetailResponse(ReviewResponse):
    """Schema for detailed review response."""
    document_title: str | None = None
    check_items: list[ReviewCheckItemStatus] = []
    finding_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
