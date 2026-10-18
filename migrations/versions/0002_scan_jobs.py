"""Añade la tabla scan_jobs (escaneos en background)

Revision ID: 0002_scan_jobs
Revises: 0001_initial
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_scan_jobs"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scan_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("target", sa.String(), nullable=True),
        sa.Column("stealth_level", sa.Integer(), nullable=True),
        sa.Column("ports", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scan_jobs_id", "scan_jobs", ["id"])
    op.create_index("ix_scan_jobs_target", "scan_jobs", ["target"])
    op.create_index("ix_scan_jobs_status", "scan_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_scan_jobs_status", table_name="scan_jobs")
    op.drop_index("ix_scan_jobs_target", table_name="scan_jobs")
    op.drop_index("ix_scan_jobs_id", table_name="scan_jobs")
    op.drop_table("scan_jobs")
