"""Service for parent-subsidiary policy comparison using LLM."""

import json

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.services.llm_service import llm_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

CHECKLIST_PROMPT = """あなたは企業規程の専門家です。
以下の親会社の規程文書を分析し、子会社の規程と比較する際にチェックすべき項目のリストを生成してください。

各チェック項目は、親会社規程に記載されている具体的な要件・規定を表します。

## 親会社規程の内容:
{parent_content}

## 出力形式（JSON）:
以下のJSON形式で出力してください。
```json
{{
  "items": [
    {{
      "item_text": "チェック項目の具体的な内容（例：情報セキュリティ責任者の設置義務）",
      "category": "カテゴリ（例：組織体制、情報管理、人事管理、コンプライアンス等）"
    }}
  ]
}}
```

重要:
- 各チェック項目は具体的かつ検証可能な内容にしてください
- 15〜30項目程度を生成してください
- カテゴリは文書の構造に基づいて分類してください
"""

COMPARISON_PROMPT = """あなたは企業規程の比較分析の専門家です。
以下のチェック項目について、親会社規程と子会社規程を比較してください。

## チェック項目:
{check_item_text}

## 親会社規程の関連部分:
{parent_content}

## 子会社規程の関連部分:
{subsidiary_content}

## 判定基準:
- COMPLIANT: 子会社規程が親会社規程の要件を満たしている
- STRICTER: 子会社規程の方がより厳格な規定になっている
- LOOSER: 子会社規程の方が緩い規定になっている
- MISSING: 子会社規程に該当する規定が存在しない
- DIFFERENT: 親子間で異なるアプローチを取っている

## 出力形式（JSON）:
```json
{{
  "status": "COMPLIANT or STRICTER or LOOSER or MISSING or DIFFERENT",
  "parent_text": "親会社規程の該当箇所のテキスト（引用）",
  "subsidiary_text": "子会社規程の該当箇所のテキスト（引用、MISSINGの場合は空文字）",
  "explanation": "判定理由の説明"
}}
```
"""


def _get_document_content(db: Session, doc: Document, max_chars: int = 8000) -> str:
    """Get document content from chunks or extracted_text."""
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc.id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )
    if chunks:
        content = "\n\n".join(str(c.content) for c in chunks)
    else:
        content: str = str(doc.extracted_text or "")
    return content[:max_chars]


async def generate_checklist(db: Session, project_id: int) -> list[dict]:
    """Generate a checklist from the parent document using LLM."""
    from app.models.comparison import ComparisonProject

    project = (
        db.query(ComparisonProject).filter(ComparisonProject.id == project_id).first()
    )
    if not project:
        raise ValueError("Project not found")

    parent_doc = (
        db.query(Document).filter(Document.id == project.parent_document_id).first()
    )
    if not parent_doc:
        raise ValueError("Parent document not found")

    parent_content = _get_document_content(db, parent_doc)
    prompt = CHECKLIST_PROMPT.format(parent_content=parent_content)

    response = await llm_service.generate(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4000,
        json_mode=True,
    )

    return _parse_checklist_response(response.content)


def _parse_checklist_response(content: str) -> list[dict]:
    """Parse LLM response into checklist items."""
    try:
        data = json.loads(content)
        return data.get("items", [])
    except json.JSONDecodeError:
        import re

        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            try:
                data = json.loads(match.group())
                return data.get("items", [])
            except json.JSONDecodeError:
                pass
    return []


async def compare_single_item(
    db: Session,
    check_item_text: str,
    parent_doc: Document,
    subsidiary_doc: Document,
) -> dict:
    """Compare a single check item between parent and subsidiary."""
    parent_content = _get_document_content(db, parent_doc)
    subsidiary_content = _get_document_content(db, subsidiary_doc)

    prompt = COMPARISON_PROMPT.format(
        check_item_text=check_item_text,
        parent_content=parent_content,
        subsidiary_content=subsidiary_content,
    )

    response = await llm_service.generate(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
        json_mode=True,
    )

    return _parse_comparison_response(response.content)


def _parse_comparison_response(content: str) -> dict:
    """Parse LLM comparison response."""
    default = {
        "status": "DIFFERENT",
        "parent_text": "",
        "subsidiary_text": "",
        "explanation": "解析に失敗しました",
    }
    try:
        data = json.loads(content)
        return {
            "status": data.get("status", "DIFFERENT"),
            "parent_text": data.get("parent_text", ""),
            "subsidiary_text": data.get("subsidiary_text", ""),
            "explanation": data.get("explanation", ""),
        }
    except json.JSONDecodeError:
        import re

        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            try:
                data = json.loads(match.group())
                return {
                    "status": data.get("status", "DIFFERENT"),
                    "parent_text": data.get("parent_text", ""),
                    "subsidiary_text": data.get("subsidiary_text", ""),
                    "explanation": data.get("explanation", ""),
                }
            except json.JSONDecodeError:
                pass
    return default
