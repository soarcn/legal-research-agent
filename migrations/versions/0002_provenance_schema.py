"""Create authoritative P2 provenance and run-audit tables.

Revision ID: 0002_provenance
Revises: 0001_initial
Create Date: 2026-09-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_provenance"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_snapshots",
        sa.Column("source_snapshot_id", sa.String(256), primary_key=True),
        sa.Column("dataset", sa.String(256), nullable=False),
        sa.Column("dataset_revision", sa.String(40), nullable=False),
        sa.Column("source_url", sa.Text, nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("corpus_sha256", sa.String(64), nullable=False),
        sa.Column("corpus_count", sa.Integer, nullable=False),
        sa.Column("qa_sha256", sa.String(64), nullable=False),
        sa.Column("qa_count", sa.Integer, nullable=False),
        sa.Column("licence_policy", sa.Text, nullable=False),
        sa.Column("jurisdiction", sa.String(32), nullable=False),
        sa.Column("language", sa.String(32), nullable=False),
        sa.Column("corpus_snapshot_date", sa.Date, nullable=True),
        sa.Column("corpus_snapshot_date_status", sa.String(64), nullable=False),
    )
    op.create_table(
        "source_passages",
        sa.Column(
            "source_snapshot_id",
            sa.String(256),
            sa.ForeignKey("source_snapshots.source_snapshot_id"),
            primary_key=True,
        ),
        sa.Column("source_passage_id", sa.String(256), primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("footnotes", sa.Text, nullable=True),
        sa.Column("content_sha256", sa.String(64), nullable=False),
    )
    op.create_table(
        "benchmark_questions",
        sa.Column(
            "source_snapshot_id",
            sa.String(256),
            sa.ForeignKey("source_snapshots.source_snapshot_id"),
            primary_key=True,
        ),
        sa.Column("question_id", sa.Integer, primary_key=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("relevant_passage_id", sa.String(256), nullable=False),
    )
    op.create_table(
        "ingestion_jobs",
        sa.Column("ingestion_job_id", sa.Uuid, primary_key=True),
        sa.Column(
            "source_snapshot_id",
            sa.String(256),
            sa.ForeignKey("source_snapshots.source_snapshot_id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_category", sa.String(128)),
    )
    op.create_table(
        "research_runs",
        sa.Column("run_id", sa.Uuid, primary_key=True),
        sa.Column(
            "source_snapshot_id",
            sa.String(256),
            sa.ForeignKey("source_snapshots.source_snapshot_id"),
            nullable=False,
        ),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("jurisdiction", sa.String(32), nullable=False),
        sa.Column("requested_effective_at", sa.Date),
        sa.Column("evidence_state", sa.String(32)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("research_runs")
    op.drop_table("ingestion_jobs")
    op.drop_table("benchmark_questions")
    op.drop_table("source_passages")
    op.drop_table("source_snapshots")
