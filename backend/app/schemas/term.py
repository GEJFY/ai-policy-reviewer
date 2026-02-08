"""Pydantic schemas for Term."""

from datetime import datetime
from pydantic import BaseModel, Field


class TermBase(BaseModel):
    """Base schema for Term."""
    term: str = Field(..., min_length=1, max_length=255, description="正式用語")
    aliases: list[str] | None = Field(default=None, description="別名・略語リスト")
    definition: str = Field(..., min_length=1, description="定義・説明")
    category: str = Field(..., min_length=1, max_length=50, description="カテゴリ（人事/財務/IT/法務/一般）")
    usage_note: str | None = Field(default=None, description="使用上の注意")


class TermCreate(TermBase):
    """Schema for creating a new term."""
    pass


class TermUpdate(BaseModel):
    """Schema for updating a term."""
    term: str | None = Field(default=None, min_length=1, max_length=255)
    aliases: list[str] | None = None
    definition: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    usage_note: str | None = None


class TermResponse(TermBase):
    """Schema for term response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TermSearchRequest(BaseModel):
    """Schema for term vector search request."""
    query: str = Field(..., min_length=1, description="検索クエリ")
    top_k: int = Field(default=10, ge=1, le=100, description="取得件数")


class TermBulkCreate(BaseModel):
    """Schema for bulk term creation."""
    terms: list[TermCreate]
