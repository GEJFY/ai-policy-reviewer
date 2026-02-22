"""Models for parent-subsidiary policy comparison."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class ComparisonProject(Base):
    """A comparison project between parent and subsidiary policies."""

    __tablename__ = "comparison_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    subsidiary_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    status = Column(
        String(50), default="created"
    )  # created / checklist_ready / comparing / completed
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    parent_document = relationship(
        "Document", foreign_keys=[parent_document_id], lazy="joined"
    )
    subsidiary_document = relationship(
        "Document", foreign_keys=[subsidiary_document_id], lazy="joined"
    )
    check_items = relationship(
        "ComparisonCheckItem",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ComparisonCheckItem.order_index",
    )
    results = relationship(
        "ComparisonResult",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ComparisonCheckItem(Base):
    """A checklist item generated from the parent policy."""

    __tablename__ = "comparison_check_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("comparison_projects.id"), nullable=False)
    item_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    order_index = Column(Integer, default=0)

    project = relationship("ComparisonProject", back_populates="check_items")
    result = relationship(
        "ComparisonResult",
        back_populates="check_item",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ComparisonResult(Base):
    """Result of comparing a single check item against subsidiary policy."""

    __tablename__ = "comparison_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("comparison_projects.id"), nullable=False)
    check_item_id = Column(
        Integer, ForeignKey("comparison_check_items.id"), nullable=False
    )
    status = Column(
        String(50), nullable=False
    )  # COMPLIANT / STRICTER / LOOSER / MISSING / DIFFERENT
    parent_text = Column(Text, nullable=True)
    subsidiary_text = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)

    project = relationship("ComparisonProject", back_populates="results")
    check_item = relationship("ComparisonCheckItem", back_populates="result")
