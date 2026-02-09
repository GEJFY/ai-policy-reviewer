"""Database initialization."""

import os
from app.db.database import engine
from app.models.base import Base


def create_tables():
    """Create all database tables."""
    # Ensure data directory exists
    data_dir = os.path.dirname(engine.url.database) if engine.url.database else "./data"
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    # Import all models to ensure they are registered with Base

    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
