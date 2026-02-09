"""Pydantic schemas for CheckItem."""

from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class CheckCategory(str, Enum):
    """Check item category enumeration."""

    TERMINOLOGY = "TERMINOLOGY"  # 用語統一
    GRAMMAR = "GRAMMAR"  # 文法・表現
    STRUCTURE = "STRUCTURE"  # 構成・体裁
    COMPLIANCE = "COMPLIANCE"  # 法令・コンプライアンス
    CONSISTENCY = "CONSISTENCY"  # 整合性
    SECURITY = "SECURITY"  # セキュリティ
    OPERATIONAL = "OPERATIONAL"  # 実務適合性


class Severity(str, Enum):
    """Severity level enumeration."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CheckItemBase(BaseModel):
    """Base schema for CheckItem."""

    name: str = Field(..., min_length=1, max_length=255, description="チェック項目名")
    category: CheckCategory = Field(..., description="カテゴリ")
    description: str = Field(..., min_length=1, description="チェック内容の説明")
    severity: Severity = Field(default=Severity.MEDIUM, description="重要度")
    prompt_template: str | None = Field(
        default=None, description="カスタムプロンプトテンプレート"
    )
    is_active: bool = Field(default=True, description="有効/無効")


class CheckItemCreate(CheckItemBase):
    """Schema for creating a new check item."""

    pass


class CheckItemUpdate(BaseModel):
    """Schema for updating a check item."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: CheckCategory | None = None
    description: str | None = Field(default=None, min_length=1)
    severity: Severity | None = None
    prompt_template: str | None = None
    is_active: bool | None = None


class CheckItemResponse(CheckItemBase):
    """Schema for check item response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
