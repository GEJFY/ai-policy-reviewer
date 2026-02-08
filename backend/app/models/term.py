"""Term model for internal terminology dictionary."""

from sqlalchemy import Column, Integer, String, Text, DateTime, LargeBinary
from sqlalchemy.sql import func

from app.models.base import Base


class Term(Base):
    """Social internal terminology dictionary."""

    __tablename__ = "terms"

    id = Column(Integer, primary_key=True, index=True)
    term = Column(String(255), nullable=False, index=True)
    aliases = Column(Text)  # JSON array: ["社員", "スタッフ"]
    definition = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)  # 人事/財務/IT/法務/一般
    usage_note = Column(Text)
    embedding = Column(LargeBinary)  # float32 array bytes for vector search
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Term(id={self.id}, term='{self.term}', category='{self.category}')>"
