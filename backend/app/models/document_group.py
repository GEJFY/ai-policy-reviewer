"""DocumentGroup and DocumentGroupMember models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class DocumentGroup(Base):
    """Group of related policy documents for consistency checking."""

    __tablename__ = "document_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    members = relationship(
        "DocumentGroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<DocumentGroup(id={self.id}, name='{self.name}')>"


class DocumentGroupMember(Base):
    """Association between document groups and documents."""

    __tablename__ = "document_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("document_groups.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    added_at = Column(DateTime, server_default=func.now())

    # Relationships
    group = relationship("DocumentGroup", back_populates="members")
    document = relationship("Document")

    def __repr__(self):
        return f"<DocumentGroupMember(group={self.group_id}, doc={self.document_id})>"


class ConsistencyCheckJob(Base):
    """Background job for consistency check execution."""

    __tablename__ = "consistency_check_jobs"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("document_groups.id"), nullable=False)
    status = Column(String(20), default="processing")  # processing/completed/failed
    total_pairs = Column(Integer, default=0)
    completed_pairs = Column(Integer, default=0)
    result_json = Column(Text)  # JSON string of findings
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

    group = relationship("DocumentGroup")

    def __repr__(self):
        return f"<ConsistencyCheckJob(id={self.id}, group={self.group_id}, status='{self.status}')>"
