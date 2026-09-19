"""Esquema inicial anonimizado.

Revision ID: 20260918_0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "20260918_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("processing_batches", sa.Column("id", sa.String(36), primary_key=True), sa.Column("case_type", sa.String(24), nullable=False), sa.Column("source", sa.String(255), nullable=False), sa.Column("seed", sa.Integer()), sa.Column("status", sa.String(16), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.CheckConstraint("case_type IN ('CASE1_LAB', 'CASE1_REACTIVA', 'CASE2')"), sa.CheckConstraint("status IN ('RUNNING', 'COMPLETED', 'FAILED')"))
    op.create_index("ix_batches_case_created", "processing_batches", ["case_type", "created_at"])
    op.create_table("companies_processed", sa.Column("id", sa.String(36), primary_key=True), sa.Column("batch_id", sa.String(36), sa.ForeignKey("processing_batches.id"), nullable=False), sa.Column("anonymous_code", sa.String(32), nullable=False), sa.Column("public_data", sa.JSON(), nullable=False), sa.Column("provenance", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("batch_id", "anonymous_code"))
    op.create_index("ix_companies_code", "companies_processed", ["anonymous_code"])
    op.create_table("financial_assessments", sa.Column("id", sa.String(36), primary_key=True), sa.Column("company_id", sa.String(36), sa.ForeignKey("companies_processed.id"), nullable=False), sa.Column("synthetic_data", sa.JSON(), nullable=False), sa.Column("score", sa.Integer(), nullable=False), sa.Column("risk_level", sa.String(8), nullable=False), sa.Column("recommendation", sa.String(16), nullable=False), sa.Column("factors", sa.JSON(), nullable=False), sa.Column("explanation", sa.Text(), nullable=False), sa.Column("prompt_version", sa.String(32), nullable=False), sa.Column("model", sa.String(128), nullable=False), sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False), sa.Column("review_status", sa.String(16), nullable=False), sa.Column("analyst_decision", sa.String(32)), sa.Column("analyst_comment", sa.Text()), sa.CheckConstraint("risk_level IN ('BAJO', 'MEDIO', 'ALTO')"), sa.CheckConstraint("recommendation IN ('APROBAR', 'EVALUAR', 'RECHAZAR')"), sa.CheckConstraint("review_status IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')"))
    op.create_index("ix_assessments_risk_review", "financial_assessments", ["risk_level", "review_status"])
    op.create_index("ix_assessments_executed", "financial_assessments", ["executed_at"])
    op.create_table("complaints", sa.Column("id", sa.String(36), primary_key=True), sa.Column("source_code", sa.String(64), nullable=False, unique=True), sa.Column("anonymized_text", sa.Text(), nullable=False), sa.Column("golden_label", sa.String(16), nullable=False), sa.Column("provenance", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.CheckConstraint("golden_label IN ('CONSULTA', 'RECLAMO', 'SOLICITUD')"))
    op.create_table("complaint_predictions", sa.Column("id", sa.String(36), primary_key=True), sa.Column("complaint_id", sa.String(36), sa.ForeignKey("complaints.id")), sa.Column("anonymized_text", sa.Text(), nullable=False), sa.Column("category", sa.String(16), nullable=False), sa.Column("confidence", sa.String(8), nullable=False), sa.Column("rationale", sa.Text(), nullable=False), sa.Column("draft_response", sa.Text(), nullable=False), sa.Column("prompt_version", sa.String(32), nullable=False), sa.Column("model", sa.String(128), nullable=False), sa.Column("latency_ms", sa.Float(), nullable=False), sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False), sa.Column("review_status", sa.String(16), nullable=False), sa.Column("analyst_decision", sa.String(32)), sa.Column("analyst_comment", sa.Text()), sa.CheckConstraint("category IN ('CONSULTA', 'RECLAMO', 'SOLICITUD')"), sa.CheckConstraint("review_status IN ('PENDIENTE', 'APROBADA', 'RECHAZADA', 'CORREGIDA')"))
    op.create_index("ix_predictions_prompt_category", "complaint_predictions", ["prompt_version", "category"])
    op.create_table("model_runs", sa.Column("id", sa.String(36), primary_key=True), sa.Column("batch_id", sa.String(36), sa.ForeignKey("processing_batches.id")), sa.Column("case_type", sa.String(24), nullable=False), sa.Column("prompt_version", sa.String(32), nullable=False), sa.Column("model", sa.String(128), nullable=False), sa.Column("provider", sa.String(16), nullable=False), sa.Column("latency_ms", sa.Float(), nullable=False), sa.Column("success", sa.Boolean(), nullable=False), sa.Column("result_summary", sa.JSON(), nullable=False), sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_model_runs_case_executed", "model_runs", ["case_type", "executed_at"])
    op.create_table("human_reviews", sa.Column("id", sa.String(36), primary_key=True), sa.Column("resource_type", sa.String(32), nullable=False), sa.Column("resource_id", sa.String(36), nullable=False), sa.Column("reviewer_object_id", sa.String(64), nullable=False), sa.Column("decision", sa.String(32), nullable=False), sa.Column("comment", sa.Text(), nullable=False), sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False), sa.CheckConstraint("resource_type IN ('FINANCIAL_ASSESSMENT', 'COMPLAINT_PREDICTION')"))
    op.create_index("ix_reviews_resource", "human_reviews", ["resource_type", "resource_id"])


def downgrade() -> None:
    for table in ["human_reviews", "model_runs", "complaint_predictions", "complaints", "financial_assessments", "companies_processed", "processing_batches"]:
        op.drop_table(table)
