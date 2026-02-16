"""Add missing columns - confidence, usage_note

Revision ID: 002
Revises: 001
Create Date: 2026-02-17

初期マイグレーション後に追加されたカラムの反映:
- review_findings.confidence (Float): AI信頼度スコア (0.0-1.0)
- terms.usage_note (Text): 用語の使い分け・注意事項
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # review_findings に confidence カラムを追加
    with op.batch_alter_table("review_findings") as batch_op:
        batch_op.add_column(sa.Column("confidence", sa.Float(), nullable=True))

    # terms に usage_note カラムを追加
    with op.batch_alter_table("terms") as batch_op:
        batch_op.add_column(sa.Column("usage_note", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("terms") as batch_op:
        batch_op.drop_column("usage_note")

    with op.batch_alter_table("review_findings") as batch_op:
        batch_op.drop_column("confidence")
