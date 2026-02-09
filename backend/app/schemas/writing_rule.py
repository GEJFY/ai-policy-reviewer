"""Pydantic schemas for WritingRule."""

from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class RuleType(str, Enum):
    """Writing rule type enumeration."""

    STYLE = "STYLE"  # 文体ルール（敬体/常体等）
    FORMAT = "FORMAT"  # フォーマットルール（日付形式、番号形式等）
    TERMINOLOGY = "TERMINOLOGY"  # 用語ルール（外来語表記等）


class WritingRuleBase(BaseModel):
    """Base schema for WritingRule."""

    name: str = Field(..., min_length=1, max_length=255, description="ルール名")
    rule_type: RuleType = Field(..., description="ルール種別")
    pattern: str | None = Field(
        default=None, description="検出パターン（正規表現または自然言語）"
    )
    correct_form: str = Field(..., min_length=1, description="正しい形式")
    example_bad: str | None = Field(default=None, description="NG例")
    example_good: str | None = Field(default=None, description="OK例")
    is_active: bool = Field(default=True, description="有効/無効")


class WritingRuleCreate(WritingRuleBase):
    """Schema for creating a new writing rule."""

    pass


class WritingRuleUpdate(BaseModel):
    """Schema for updating a writing rule."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    rule_type: RuleType | None = None
    pattern: str | None = None
    correct_form: str | None = Field(default=None, min_length=1)
    example_bad: str | None = None
    example_good: str | None = None
    is_active: bool | None = None


class WritingRuleResponse(WritingRuleBase):
    """Schema for writing rule response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
