"""Schemas for parent-subsidiary policy comparison."""

from pydantic import BaseModel, Field
from datetime import datetime


class ComparisonProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    parent_document_id: int


class ComparisonProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class SetSubsidiaryRequest(BaseModel):
    subsidiary_document_id: int


class CheckItemEdit(BaseModel):
    item_text: str = Field(..., min_length=1)
    category: str | None = None


class ChecklistEditRequest(BaseModel):
    items: list[CheckItemEdit]


class ComparisonCheckItemResponse(BaseModel):
    id: int
    item_text: str
    category: str | None
    order_index: int

    class Config:
        from_attributes = True


class ComparisonResultResponse(BaseModel):
    id: int
    check_item_id: int
    check_item_text: str = ""
    status: str
    parent_text: str | None
    subsidiary_text: str | None
    explanation: str | None

    class Config:
        from_attributes = True


class ComparisonProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    parent_document_id: int
    parent_document_title: str = ""
    subsidiary_document_id: int | None
    subsidiary_document_title: str | None = None
    status: str
    check_item_count: int = 0
    result_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComparisonProjectDetailResponse(ComparisonProjectResponse):
    check_items: list[ComparisonCheckItemResponse] = []
    results: list[ComparisonResultResponse] = []


class ComparisonExportResponse(BaseModel):
    message: str
