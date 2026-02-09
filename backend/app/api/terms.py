"""API endpoints for Term management."""

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.term import Term
from app.schemas.term import (
    TermCreate,
    TermUpdate,
    TermResponse,
    TermSearchRequest,
    TermBulkCreate,
)
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api/v1/terms", tags=["Terms"])


@router.get("", response_model=list[TermResponse])
async def list_terms(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get list of terms with optional filtering."""
    query = db.query(Term)

    if category:
        query = query.filter(Term.category == category)

    terms = query.offset(skip).limit(limit).all()

    # Convert aliases from JSON string to list
    for term in terms:
        if term.aliases and isinstance(term.aliases, str):
            try:
                term.aliases = json.loads(term.aliases)
            except json.JSONDecodeError:
                term.aliases = []

    return terms


@router.get("/{term_id}", response_model=TermResponse)
async def get_term(term_id: int, db: Session = Depends(get_db)):
    """Get a specific term by ID."""
    term = db.query(Term).filter(Term.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")

    # Convert aliases from JSON string to list
    if term.aliases and isinstance(term.aliases, str):
        try:
            term.aliases = json.loads(term.aliases)
        except json.JSONDecodeError:
            term.aliases = []

    return term


@router.post("", response_model=TermResponse, status_code=201)
async def create_term(term_data: TermCreate, db: Session = Depends(get_db)):
    """Create a new term."""
    # Check for duplicate term
    existing = db.query(Term).filter(Term.term == term_data.term).first()
    if existing:
        raise HTTPException(status_code=400, detail="Term already exists")

    # Convert aliases list to JSON string
    aliases_json = json.dumps(term_data.aliases) if term_data.aliases else None

    # Generate embedding if service is available
    embedding_bytes = None
    if embedding_service.is_available():
        try:
            embed_text = f"{term_data.term}: {term_data.definition}"
            embedding = await embedding_service.get_embedding(embed_text)
            embedding_bytes = embedding_service.embedding_to_bytes(embedding)
        except Exception as e:
            print(f"Warning: Failed to generate embedding: {e}")

    # Create term
    db_term = Term(
        term=term_data.term,
        aliases=aliases_json,
        definition=term_data.definition,
        category=term_data.category,
        usage_note=term_data.usage_note,
        embedding=embedding_bytes,
    )

    db.add(db_term)
    db.commit()
    db.refresh(db_term)

    # Convert aliases back to list for response
    if db_term.aliases:
        db_term.aliases = json.loads(db_term.aliases)

    return db_term


@router.put("/{term_id}", response_model=TermResponse)
async def update_term(
    term_id: int, term_data: TermUpdate, db: Session = Depends(get_db)
):
    """Update an existing term."""
    db_term = db.query(Term).filter(Term.id == term_id).first()
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")

    # Update fields
    update_data = term_data.model_dump(exclude_unset=True)

    # Handle aliases conversion
    if "aliases" in update_data and update_data["aliases"] is not None:
        update_data["aliases"] = json.dumps(update_data["aliases"])

    for field, value in update_data.items():
        setattr(db_term, field, value)

    # Regenerate embedding if term or definition changed
    if (
        "term" in update_data or "definition" in update_data
    ) and embedding_service.is_available():
        try:
            embed_text = f"{db_term.term}: {db_term.definition}"
            embedding = await embedding_service.get_embedding(embed_text)
            db_term.embedding = embedding_service.embedding_to_bytes(embedding)
        except Exception as e:
            print(f"Warning: Failed to regenerate embedding: {e}")

    db.commit()
    db.refresh(db_term)

    # Convert aliases back to list for response
    if db_term.aliases and isinstance(db_term.aliases, str):
        db_term.aliases = json.loads(db_term.aliases)

    return db_term


@router.delete("/{term_id}", status_code=204)
async def delete_term(term_id: int, db: Session = Depends(get_db)):
    """Delete a term."""
    db_term = db.query(Term).filter(Term.id == term_id).first()
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")

    db.delete(db_term)
    db.commit()
    return None


@router.post("/search", response_model=list[TermResponse])
async def search_terms(
    request: TermSearchRequest,
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Search for similar terms using vector similarity."""
    if not embedding_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Embedding service not available. Check Azure OpenAI configuration.",
        )

    try:
        # Generate query embedding
        query_embedding = await embedding_service.get_embedding(request.query)

        # Search for similar terms
        results = vector_store.search_similar_terms(
            db=db,
            query_embedding=query_embedding,
            top_k=request.top_k,
            category=category,
        )

        # Extract terms and convert aliases
        terms = []
        for term, score in results:
            if term.aliases and isinstance(term.aliases, str):
                try:
                    term.aliases = json.loads(term.aliases)
                except json.JSONDecodeError:
                    term.aliases = []
            terms.append(term)

        return terms

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/bulk", response_model=list[TermResponse], status_code=201)
async def bulk_create_terms(request: TermBulkCreate, db: Session = Depends(get_db)):
    """Create multiple terms at once."""
    created_terms = []

    for term_data in request.terms:
        # Skip duplicates
        existing = db.query(Term).filter(Term.term == term_data.term).first()
        if existing:
            continue

        # Convert aliases
        aliases_json = json.dumps(term_data.aliases) if term_data.aliases else None

        # Generate embedding
        embedding_bytes = None
        if embedding_service.is_available():
            try:
                embed_text = f"{term_data.term}: {term_data.definition}"
                embedding = await embedding_service.get_embedding(embed_text)
                embedding_bytes = embedding_service.embedding_to_bytes(embedding)
            except Exception:
                pass

        db_term = Term(
            term=term_data.term,
            aliases=aliases_json,
            definition=term_data.definition,
            category=term_data.category,
            usage_note=term_data.usage_note,
            embedding=embedding_bytes,
        )
        db.add(db_term)
        created_terms.append(db_term)

    db.commit()

    # Refresh and convert aliases
    for term in created_terms:
        db.refresh(term)
        if term.aliases and isinstance(term.aliases, str):
            term.aliases = json.loads(term.aliases)

    return created_terms
