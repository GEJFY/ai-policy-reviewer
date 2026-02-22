"""API endpoints for WritingRule management."""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.writing_rule import WritingRule
from app.schemas.writing_rule import (
    WritingRuleCreate,
    WritingRuleUpdate,
    WritingRuleResponse,
    RuleType,
)
from app.services.csv_import_service import (
    read_import_file,
    validate_required_columns,
    generate_csv_template,
    WRITING_RULE_HEADERS,
    WRITING_RULE_SAMPLE,
)

router = APIRouter(prefix="/api/v1/writing-rules", tags=["Writing Rules"])


@router.get("", response_model=list[WritingRuleResponse])
async def list_writing_rules(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    rule_type: Optional[RuleType] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get list of writing rules with optional filtering."""
    query = db.query(WritingRule)

    if rule_type:
        query = query.filter(WritingRule.rule_type == rule_type.value)

    if is_active is not None:
        query = query.filter(WritingRule.is_active == is_active)

    return query.offset(skip).limit(limit).all()


@router.get("/types")
async def get_rule_types():
    """Get list of available rule types."""
    return [{"value": rt.value, "label": _get_type_label(rt)} for rt in RuleType]


@router.get("/{rule_id}", response_model=WritingRuleResponse)
async def get_writing_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get a specific writing rule by ID."""
    rule = db.query(WritingRule).filter(WritingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Writing rule not found")
    return rule


@router.post("", response_model=WritingRuleResponse, status_code=201)
async def create_writing_rule(
    rule_data: WritingRuleCreate, db: Session = Depends(get_db)
):
    """Create a new writing rule."""
    db_rule = WritingRule(
        name=rule_data.name,
        rule_type=rule_data.rule_type.value,
        pattern=rule_data.pattern,
        correct_form=rule_data.correct_form,
        example_bad=rule_data.example_bad,
        example_good=rule_data.example_good,
        is_active=rule_data.is_active,
    )

    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)

    return db_rule


@router.put("/{rule_id}", response_model=WritingRuleResponse)
async def update_writing_rule(
    rule_id: int, rule_data: WritingRuleUpdate, db: Session = Depends(get_db)
):
    """Update an existing writing rule."""
    db_rule = db.query(WritingRule).filter(WritingRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Writing rule not found")

    update_data = rule_data.model_dump(exclude_unset=True)

    # Convert enum to value
    if "rule_type" in update_data and update_data["rule_type"] is not None:
        update_data["rule_type"] = update_data["rule_type"].value

    for field, value in update_data.items():
        setattr(db_rule, field, value)

    db.commit()
    db.refresh(db_rule)

    return db_rule


@router.delete("/{rule_id}", status_code=204)
async def delete_writing_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a writing rule."""
    db_rule = db.query(WritingRule).filter(WritingRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Writing rule not found")

    db.delete(db_rule)
    db.commit()
    return None


def _get_type_label(rule_type: RuleType) -> str:
    """Get Japanese label for rule type."""
    labels = {
        RuleType.STYLE: "文体ルール",
        RuleType.FORMAT: "フォーマットルール",
        RuleType.TERMINOLOGY: "用語ルール",
    }
    return labels.get(rule_type, rule_type.value)


@router.get("/template")
async def download_writing_rule_template():
    """Download CSV template for writing rule import."""
    content = generate_csv_template(WRITING_RULE_HEADERS, WRITING_RULE_SAMPLE)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=writing_rules_template.csv"
        },
    )


@router.post("/import")
async def import_writing_rules(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import writing rules from CSV or Excel file."""
    filename = file.filename or "import.csv"
    file_bytes = await file.read()

    rows, errors = read_import_file(file_bytes, filename)
    if errors:
        return {"success": 0, "errors": errors}

    col_errors = validate_required_columns(rows, ["name", "rule_type", "correct_form"])
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

        db_rule = WritingRule(
            name=name,
            rule_type=row.get("rule_type", "STYLE"),
            pattern=row.get("pattern", "") or None,
            correct_form=row.get("correct_form", ""),
            example_bad=row.get("example_bad", "") or None,
            example_good=row.get("example_good", "") or None,
            is_active=is_active,
        )
        db.add(db_rule)
        success += 1

    if success > 0:
        db.commit()

    return {"success": success, "errors": row_errors}
