"""WritingRule model for document writing rules."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func

from app.models.base import Base


class WritingRule(Base):
    """Document writing rule definition."""

    __tablename__ = "writing_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)  # STYLE/FORMAT/TERMINOLOGY
    pattern = Column(Text)  # Detection pattern (regex or natural language)
    correct_form = Column(Text, nullable=False)  # Correct format/style
    example_bad = Column(Text)  # NG example
    example_good = Column(Text)  # OK example
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<WritingRule(id={self.id}, name='{self.name}', type='{self.rule_type}')>"
