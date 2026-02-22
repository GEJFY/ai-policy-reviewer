"""Pydantic schemas for Document."""

from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class OCRStatus(str, Enum):
    """OCR processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentBase(BaseModel):
    """Base schema for Document."""

    title: str = Field(..., min_length=1, max_length=500, description="文書タイトル")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document (via file upload)."""

    pass


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    id: int
    file_path: str
    file_type: str | None
    extracted_text: str | None
    ocr_status: str
    ocr_progress: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response."""

    id: int
    document_id: int
    chunk_index: int
    section_title: str | None = None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    id: int
    title: str
    file_path: str
    ocr_status: str
    message: str
