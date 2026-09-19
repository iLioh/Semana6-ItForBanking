"""Contratos HTTP de los dos casos oficiales."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.app.ai import ComplaintClassification, ExplainabilityResult, KYCResult, ScoringResult


class RunCase1Request(BaseModel):
    company_id: str | None = Field(default=None, pattern=r"^EMPRESA_\d{3}$")


class BatchResponse(BaseModel):
    batch_id: str
    status: str
    processed: int


class AssessmentResponse(BaseModel):
    id: str
    batch_id: str
    company_code: str
    company_name: str
    public_variables: dict
    synthetic_variables: dict
    kyc: KYCResult
    scoring: ScoringResult
    xai: ExplainabilityResult
    reference_score: int
    scoring_discrepancy: bool
    requires_human_review: bool
    kyc_reference: str
    kyc_discrepancy: bool
    score: int
    risk_level: str
    recommendation: str
    prompt_versions: dict[str, str]
    model: str
    executed_at: datetime
    review_status: Literal["PENDIENTE", "REVISADA"]
    human_decision: Literal["APROBAR", "EVALUAR", "RECHAZAR"] | None
    analyst_comment: str | None


class PaginatedAssessments(BaseModel):
    items: list[AssessmentResponse]
    page: int
    page_size: int
    total: int


class ReviewBase(BaseModel):
    comment: str = Field(min_length=3, max_length=1000)

    @field_validator("comment")
    @classmethod
    def no_control_characters(cls, value: str) -> str:
        cleaned = value.strip()
        if any(ord(character) < 32 and character not in "\n\t" for character in cleaned):
            raise ValueError("El texto contiene caracteres de control")
        return cleaned


class Case1ReviewRequest(ReviewBase):
    human_decision: Literal["APROBAR", "EVALUAR", "RECHAZAR"]


class Case2ReviewRequest(ReviewBase):
    decision: Literal["VALIDAR", "CORREGIR", "RECHAZAR_BORRADOR"]
    human_category_correction: Literal["FRAUDE", "SERVICIO", "PRODUCTO"] | None = None


class ComplaintClassifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str = Field(pattern=r"^QUEJA_\d{3}$")
    prompt_version: Literal["classification_v1", "classification_v2"] = "classification_v2"


class ComplaintPredictionResponse(ComplaintClassification):
    id: str
    case_id: str
    draft_response: str
    prompt_version: str
    response_prompt_version: str | None
    model: str
    latency_ms: float
    executed_at: datetime
    review_status: Literal["PENDIENTE", "REVISADA"]
    analyst_decision: str | None = None
    human_category_correction: str | None = None
    analyst_comment: str | None = None


class EvaluationRequest(BaseModel):
    prompt_versions: list[Literal["classification_v1", "classification_v2"]] = [
        "classification_v1", "classification_v2"
    ]

    @field_validator("prompt_versions")
    @classmethod
    def both_versions(cls, value: list[str]) -> list[str]:
        if len(value) != 2 or set(value) != {"classification_v1", "classification_v2"}:
            raise ValueError("La comparación requiere V1 y V2 exactamente una vez")
        return value


class ClassMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    support: int


class PromptMetrics(BaseModel):
    prompt_version: str
    provider: str
    model: str
    dataset: str
    accuracy: float
    per_class: dict[str, ClassMetrics]
    precision_macro: float
    recall_macro: float
    f1_macro: float
    confusion_matrix: dict[str, dict[str, int]]
    errors: list[dict]


class MetricsResponse(BaseModel):
    evaluations: list[PromptMetrics]
    generated_at: datetime


class ErrorResponse(BaseModel):
    error: str
    detail: str
    correlation_id: str
