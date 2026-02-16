"""Review and ReviewFinding models."""

from sqlalchemy import Column, Float, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Review(Base):
    """Review session."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    status = Column(
        String(20), default="pending"
    )  # pending/processing/completed/failed
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

    # Relationships
    document = relationship("Document", back_populates="reviews")
    check_items = relationship(
        "ReviewCheckItem", back_populates="review", cascade="all, delete-orphan"
    )
    findings = relationship(
        "ReviewFinding", back_populates="review", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Review(id={self.id}, doc_id={self.document_id}, status='{self.status}')>"
        )


class ReviewCheckItem(Base):
    """Association between review and check items."""

    __tablename__ = "review_check_items"

    review_id = Column(Integer, ForeignKey("reviews.id"), primary_key=True)
    check_item_id = Column(Integer, ForeignKey("check_items.id"), primary_key=True)
    status = Column(String(20), default="pending")  # pending/processing/completed

    # Relationships
    review = relationship("Review", back_populates="check_items")

    def __repr__(self):
        return f"<ReviewCheckItem(review={self.review_id}, check={self.check_item_id})>"


class ReviewFinding(Base):
    """Review finding/issue."""

    __tablename__ = "review_findings"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    check_item_id = Column(Integer, ForeignKey("check_items.id"))
    location = Column(String(255))  # Location in document (section, line, etc.)
    original_text = Column(Text)  # Problematic text
    issue_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # HIGH/MEDIUM/LOW
    description = Column(Text, nullable=False)
    suggestion = Column(Text)  # Suggested correction
    rationale = Column(Text)  # Reason for the finding
    confidence = Column(Float)  # AI confidence score (0.0-1.0)
    status = Column(String(20), default="PENDING")  # PENDING/APPROVED/REJECTED/DEFERRED
    reviewed_by = Column(String(255))
    reviewed_at = Column(DateTime)
    comment = Column(Text)  # Reviewer's comment
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    review = relationship("Review", back_populates="findings")

    def __repr__(self):
        return f"<ReviewFinding(id={self.id}, type='{self.issue_type}', severity='{self.severity}')>"
