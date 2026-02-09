"""CheckItem model for review check items."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func

from app.models.base import Base


class CheckItem(Base):
    """Review check item definition."""

    __tablename__ = "check_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    # TERMINOLOGY/GRAMMAR/STRUCTURE/COMPLIANCE/CONSISTENCY/SECURITY/OPERATIONAL
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="MEDIUM")  # HIGH/MEDIUM/LOW
    prompt_template = Column(Text)  # Custom prompt template for this check
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (
            f"<CheckItem(id={self.id}, name='{self.name}', category='{self.category}')>"
        )
