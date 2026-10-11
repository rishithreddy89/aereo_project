"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "certificate_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_name", sa.String(255), nullable=False),
        sa.Column("certificate_title", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("issue_date", sa.String(10), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PROCESSING", "COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("total_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "certificates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("certificate_jobs.id"), nullable=False),
        sa.Column("recipient_name", sa.String(255), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("certificate_number", sa.String(50), unique=True, nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    op.create_index("ix_certificates_job_id", "certificates", ["job_id"])
    op.create_index("ix_certificates_status", "certificates", ["status"])


def downgrade() -> None:
    op.drop_table("certificates")
    op.drop_table("certificate_jobs")
