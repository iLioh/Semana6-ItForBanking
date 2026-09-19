"""Modelo relacional anonimizado y auditable."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProcessingBatch(Base):
    __tablename__ = "processing_batches"
    __table_args__ = (
        CheckConstraint("case_type IN ('CASE1_OFFICIAL', 'CASE2')"),
        CheckConstraint("status IN ('RUNNING', 'COMPLETED', 'FAILED')"),
        Index("ix_batches_case_created", "case_type", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    case_type: Mapped[str] = mapped_column(String(24), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="RUNNING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CompanyProcessed(Base):
    __tablename__ = "companies_processed"
    __table_args__ = (
        UniqueConstraint("batch_id", "anonymous_code"),
        Index("ix_companies_code", "anonymous_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    batch_id: Mapped[str] = mapped_column(ForeignKey("processing_batches.id"), nullable=False)
    anonymous_code: Mapped[str] = mapped_column(String(32), nullable=False)
    public_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    assessments: Mapped[list[FinancialAssessment]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class FinancialAssessment(Base):
    __tablename__ = "financial_assessments"
    __table_args__ = (
        CheckConstraint("risk_level IN ('BAJO', 'MEDIO', 'ALTO')"),
        CheckConstraint("recommendation IN ('APROBAR', 'EVALUAR', 'RECHAZAR')"),
        CheckConstraint("review_status IN ('PENDIENTE', 'REVISADA')"),
        Index("ix_assessments_risk_review", "risk_level", "review_status"),
        Index("ix_assessments_executed", "executed_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies_processed.id"), nullable=False)
    synthetic_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(8), nullable=False)
    recommendation: Mapped[str] = mapped_column(String(16), nullable=False)
    factors: Mapped[list] = mapped_column(JSON, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_versions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    kyc_result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    scoring_result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    xai_result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reference_score: Mapped[int | None] = mapped_column(Integer)
    scoring_discrepancy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    kyc_reference: Mapped[str | None] = mapped_column(String(16))
    kyc_discrepancy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    review_status: Mapped[str] = mapped_column(String(16), default="PENDIENTE", nullable=False)
    human_decision: Mapped[str | None] = mapped_column("analyst_decision", String(32))
    analyst_comment: Mapped[str | None] = mapped_column(Text)
    company: Mapped[CompanyProcessed] = relationship(back_populates="assessments")


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (CheckConstraint("golden_label IN ('FRAUDE', 'SERVICIO', 'PRODUCTO')"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    anonymized_text: Mapped[str] = mapped_column(Text, nullable=False)
    golden_label: Mapped[str] = mapped_column(String(16), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), nullable=False, default="FACIL")
    provenance: Mapped[str] = mapped_column(
        String(64), default="SIMULADO_OFICIAL", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ComplaintPrediction(Base):
    __tablename__ = "complaint_predictions"
    __table_args__ = (
        CheckConstraint("category IN ('FRAUDE', 'SERVICIO', 'PRODUCTO')"),
        CheckConstraint("review_status IN ('PENDIENTE', 'REVISADA')"),
        Index("ix_predictions_prompt_category", "prompt_version", "category"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    complaint_id: Mapped[str | None] = mapped_column(ForeignKey("complaints.id"))
    anonymized_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[str] = mapped_column(String(8), nullable=False)
    priority: Mapped[str] = mapped_column(String(8), nullable=False, default="MEDIA")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    secondary_category: Mapped[str] = mapped_column(String(16), nullable=False, default="NINGUNA")
    ambiguity_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    draft_response: Mapped[str] = mapped_column(Text, nullable=False)
    response_prompt_version: Mapped[str | None] = mapped_column(String(32))
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    review_status: Mapped[str] = mapped_column(String(16), default="PENDIENTE", nullable=False)
    analyst_decision: Mapped[str | None] = mapped_column(String(32))
    human_category_correction: Mapped[str | None] = mapped_column(String(16))
    analyst_comment: Mapped[str | None] = mapped_column(Text)


class ModelRun(Base):
    __tablename__ = "model_runs"
    __table_args__ = (Index("ix_model_runs_case_executed", "case_type", "executed_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    batch_id: Mapped[str | None] = mapped_column(ForeignKey("processing_batches.id"))
    case_type: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(16), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    result_summary: Mapped[dict] = mapped_column(JSON, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class HumanReview(Base):
    __tablename__ = "human_reviews"
    __table_args__ = (
        CheckConstraint("resource_type IN ('FINANCIAL_ASSESSMENT', 'COMPLAINT_PREDICTION')"),
        Index("ix_reviews_resource", "resource_type", "resource_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False)
    reviewer_object_id: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
