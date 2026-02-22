"""Database initialization."""

import os
from sqlalchemy import inspect, text
from app.db.database import engine, SessionLocal
from app.models.base import Base
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _migrate_sqlite_schema():
    """Add missing columns to existing SQLite tables.

    SQLAlchemy の create_all() は既存テーブルに新カラムを追加しないため、
    モデル定義とDBスキーマを比較し、不足カラムを ALTER TABLE で追加する。
    """
    if not engine.url.drivername.startswith("sqlite"):
        return

    inspector = inspect(engine)
    for table_name, table in Base.metadata.tables.items():
        if not inspector.has_table(table_name):
            continue

        existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
        for column in table.columns:
            if column.name not in existing_cols:
                col_type = column.type.compile(engine.dialect)
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}"
                        )
                    )
                logger.info(
                    f"Schema migration: added column {table_name}.{column.name} ({col_type})"
                )


def _seed_initial_data():
    """Seed initial check items and writing rules if tables are empty."""
    from app.models.check_item import CheckItem
    from app.db.seed_data import seed_check_items, seed_writing_rules

    db = SessionLocal()
    try:
        count = db.query(CheckItem).count()
        if count == 0:
            added = seed_check_items(db)
            logger.info(f"Seeded {added} check items")
            added = seed_writing_rules(db)
            logger.info(f"Seeded {added} writing rules")
    except Exception as e:
        logger.warning(f"Seed data insertion failed: {e}")
    finally:
        db.close()


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

    # Migrate schema for existing tables (add missing columns)
    _migrate_sqlite_schema()

    # Seed initial data if tables are empty
    _seed_initial_data()
