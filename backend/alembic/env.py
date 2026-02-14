"""
Alembic migration environment configuration.

Settings からデータベースURLを動的に取得し、
SQLAlchemy モデルのメタデータに基づいてマイグレーションを実行する。
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.config import settings
from app.models.base import Base

# 全モデルをimport（Alembicがテーブルを検出するため）
from app.models.document import Document, DocumentChunk  # noqa: F401
from app.models.review import Review, ReviewCheckItem, ReviewFinding  # noqa: F401
from app.models.check_item import CheckItem  # noqa: F401
from app.models.term import Term  # noqa: F401
from app.models.writing_rule import WritingRule  # noqa: F401

# Alembic Config object
config = context.config

# ログ設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy metadata（autogenerate用）
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    SQLを直接出力する（DB接続不要）。
    """
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    DB接続を使用してマイグレーションを実行する。
    """
    # SQLite用の接続引数
    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    configuration = {
        "sqlalchemy.url": settings.database_url,
    }

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
