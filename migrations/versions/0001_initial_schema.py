"""Esquema inicial: tabla scans

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-18

Representa el estado previo a Alembic (la tabla `scans` existía ya vía
create_all). Para BDs existentes se adopta con `alembic stamp 0001_initial`.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("target", sa.String(), nullable=True),
        sa.Column("stealth_level", sa.Integer(), nullable=True),
        sa.Column("best_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("findings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attack_roadmap", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("scan_hash", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scans_id", "scans", ["id"])
    op.create_index("ix_scans_target", "scans", ["target"])
    op.create_index("ix_scans_scan_hash", "scans", ["scan_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_scans_scan_hash", table_name="scans")
    op.drop_index("ix_scans_target", table_name="scans")
    op.drop_index("ix_scans_id", table_name="scans")
    op.drop_table("scans")
