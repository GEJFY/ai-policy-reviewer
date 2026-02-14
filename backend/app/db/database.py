"""Database connection and session management.

SQLite（ローカル開発）およびPostgreSQL（クラウド/本番）に対応。
DATABASE_URLに基づいて適切な接続設定を自動選択する。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings

# Create engine
# DB種別に応じた接続設定を適用
if settings.database_url.startswith("postgresql"):
    # PostgreSQL: 接続プール設定（本番向け）
    engine = create_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.debug,
    )
else:
    # SQLite: マルチスレッド対応
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
