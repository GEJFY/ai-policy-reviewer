"""Add section_title to document_chunks

Revision ID: 003
Revises: 002
Create Date: 2026-02-17

document_chunks にセクションタイトルカラムを追加。
階層的チャンキングでセクション情報を保持するため。
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("document_chunks") as batch_op:
        batch_op.add_column(sa.Column("section_title", sa.String(500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("document_chunks") as batch_op:
        batch_op.drop_column("section_title")
