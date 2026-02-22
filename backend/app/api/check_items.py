"""API endpoints for CheckItem management."""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.check_item import CheckItem
from app.schemas.check_item import (
    CheckItemCreate,
    CheckItemUpdate,
    CheckItemResponse,
    CheckCategory,
)
from app.services.csv_import_service import (
    read_import_file,
    validate_required_columns,
    generate_csv_template,
    CHECK_ITEM_HEADERS,
    CHECK_ITEM_SAMPLE,
)

router = APIRouter(prefix="/api/v1/check-items", tags=["Check Items"])


@router.get("", response_model=list[CheckItemResponse])
async def list_check_items(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    category: Optional[CheckCategory] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get list of check items with optional filtering."""
    query = db.query(CheckItem)

    if category:
        query = query.filter(CheckItem.category == category.value)

    if is_active is not None:
        query = query.filter(CheckItem.is_active == is_active)

    return query.offset(skip).limit(limit).all()


@router.get("/categories")
async def get_categories():
    """Get list of available check item categories."""
    return [
        {"value": cat.value, "label": _get_category_label(cat)} for cat in CheckCategory
    ]


@router.get("/{item_id}", response_model=CheckItemResponse)
async def get_check_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific check item by ID."""
    item = db.query(CheckItem).filter(CheckItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Check item not found")
    return item


@router.post("", response_model=CheckItemResponse, status_code=201)
async def create_check_item(item_data: CheckItemCreate, db: Session = Depends(get_db)):
    """Create a new check item."""
    db_item = CheckItem(
        name=item_data.name,
        category=item_data.category.value,
        description=item_data.description,
        severity=item_data.severity.value,
        prompt_template=item_data.prompt_template,
        is_active=item_data.is_active,
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


@router.put("/{item_id}", response_model=CheckItemResponse)
async def update_check_item(
    item_id: int, item_data: CheckItemUpdate, db: Session = Depends(get_db)
):
    """Update an existing check item."""
    db_item = db.query(CheckItem).filter(CheckItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Check item not found")

    update_data = item_data.model_dump(exclude_unset=True)

    # Convert enums to values
    if "category" in update_data and update_data["category"] is not None:
        update_data["category"] = update_data["category"].value
    if "severity" in update_data and update_data["severity"] is not None:
        update_data["severity"] = update_data["severity"].value

    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)

    return db_item


@router.delete("/{item_id}", status_code=204)
async def delete_check_item(item_id: int, db: Session = Depends(get_db)):
    """Delete a check item."""
    db_item = db.query(CheckItem).filter(CheckItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Check item not found")

    db.delete(db_item)
    db.commit()
    return None


def _get_category_label(category: CheckCategory) -> str:
    """Get Japanese label for category."""
    labels = {
        CheckCategory.TERMINOLOGY: "用語統一",
        CheckCategory.GRAMMAR: "文法・表現",
        CheckCategory.STRUCTURE: "構成・体裁",
        CheckCategory.COMPLIANCE: "法令・コンプライアンス",
        CheckCategory.CONSISTENCY: "整合性",
        CheckCategory.SECURITY: "セキュリティ",
        CheckCategory.OPERATIONAL: "実務適合性",
    }
    return labels.get(category, category.value)


@router.get("/template")
async def download_check_item_template():
    """Download CSV template for check item import."""
    content = generate_csv_template(CHECK_ITEM_HEADERS, CHECK_ITEM_SAMPLE)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=check_items_template.csv"
        },
    )


@router.post("/import")
async def import_check_items(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import check items from CSV or Excel file."""
    filename = file.filename or "import.csv"
    file_bytes = await file.read()

    rows, errors = read_import_file(file_bytes, filename)
    if errors:
        return {"success": 0, "errors": errors}

    col_errors = validate_required_columns(rows, ["name", "category", "description"])
    if col_errors:
        return {"success": 0, "errors": col_errors}

    success = 0
    row_errors: list[str] = []

    for i, row in enumerate(rows, start=2):
        name = row.get("name", "").strip()
        if not name:
            row_errors.append(f"行{i}: nameが空です")
            continue

        is_active_str = row.get("is_active", "true").lower()
        is_active = is_active_str not in ("false", "0", "no")

        db_item = CheckItem(
            name=name,
            category=row.get("category", "TERMINOLOGY"),
            description=row.get("description", ""),
            severity=row.get("severity", "MEDIUM"),
            prompt_template=row.get("prompt_template", "") or None,
            is_active=is_active,
        )
        db.add(db_item)
        success += 1

    if success > 0:
        db.commit()

    return {"success": success, "errors": row_errors}
