"""Document and DocumentChunk models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Document(Base):
    """Uploaded document for review."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50))  # pdf, docx, etc.
    extracted_text = Column(Text)
    ocr_status = Column(
        String(20), default="pending"
    )  # pending/processing/completed/failed
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    reviews = relationship("Review", back_populates="document")

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', status='{self.ocr_status}')>"


class DocumentChunk(Base):
    """Document chunk for vector search."""

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    section_title = Column(String(500))  # Section header (e.g. "第1条", "第2章")
    content = Column(Text, nullable=False)
    embedding = Column(LargeBinary)  # float32 array bytes
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"
