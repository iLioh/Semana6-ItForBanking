"""Rutas HTTP versionadas del laboratorio."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.app import case1, case2
from src.app.auth import Principal, require_roles
from src.app.config import get_settings
from src.app.database import get_session
from src.app.schemas import (
    AssessmentResponse,
    BatchResponse,
    Case1ReviewRequest,
    Case2ReviewRequest,
    ComplaintClassifyRequest,
    ComplaintPredictionResponse,
    EvaluationRequest,
    MetricsResponse,
    PaginatedAssessments,
    RunCase1Request,
)

router = APIRouter(prefix="/api/v1")
SessionDep = Annotated[Session, Depends(get_session)]
Analyst = Annotated[Principal, Depends(require_roles("Analyst", "Reviewer"))]
Reviewer = Annotated[Principal, Depends(require_roles("Reviewer"))]
DEMO_REVIEW_COMMENTS = {
    "Revision humana completada.",
    "Pendiente de validacion adicional.",
    "Resultado rechazado por revision humana.",
}


def _validate_demo_review(review: Case1ReviewRequest | Case2ReviewRequest) -> None:
    if get_settings().environment == "azure-demo" and review.comment not in DEMO_REVIEW_COMMENTS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "En la demo use un comentario de revision predefinido sin datos personales",
        )


@router.get("/case1/companies")
def list_case1_companies(_: Analyst) -> list[dict[str, str]]:
    return case1.list_companies()


@router.post("/case1/run", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def run_case1(request: RunCase1Request, session: SessionDep, _: Analyst) -> BatchResponse:
    try:
        batch_id, processed = case1.run_official_cases(session, request.company_id)
    except FileNotFoundError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    return BatchResponse(batch_id=batch_id, status="COMPLETED", processed=processed)


@router.get("/case1/results", response_model=PaginatedAssessments)
def list_case1_results(
    session: SessionDep,
    _: Analyst,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    risk_level: Literal["BAJO", "MEDIO", "ALTO"] | None = None,
    review_status: Literal["PENDIENTE", "REVISADA"] | None = None,
) -> PaginatedAssessments:
    items, total = case1.list_assessments(session, page, page_size, risk_level, review_status)
    return PaginatedAssessments(items=items, page=page, page_size=page_size, total=total)


@router.get("/case1/results/{assessment_id}", response_model=AssessmentResponse)
def get_case1_result(assessment_id: str, session: SessionDep, _: Analyst) -> dict:
    result = case1.get_assessment(session, assessment_id)
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evaluacion no encontrada")
    return result


@router.patch("/case1/results/{assessment_id}/human-review", response_model=AssessmentResponse)
def review_case1_result(
    assessment_id: str,
    review: Case1ReviewRequest,
    session: SessionDep,
    reviewer: Reviewer,
) -> dict:
    _validate_demo_review(review)
    try:
        result = case1.review_assessment(session, assessment_id, review, reviewer.object_id)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evaluacion no encontrada")
    return result


@router.post("/case2/classify", response_model=ComplaintPredictionResponse, status_code=201)
def classify_complaint(
    request: ComplaintClassifyRequest, session: SessionDep, _: Analyst
) -> dict:
    try:
        prediction = case2.classify_prepared_case(session, request.case_id, request.prompt_version)
    except FileNotFoundError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    return case2.serialize_prediction(prediction)


@router.get("/case2/cases")
def list_prepared_cases(_: Analyst) -> list[dict[str, str]]:
    try:
        return case2.list_prepared_cases()
    except FileNotFoundError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error


@router.post("/case2/evaluate", response_model=MetricsResponse)
def evaluate_case2(request: EvaluationRequest, session: SessionDep, _: Analyst) -> dict:
    try:
        return case2.evaluate_prompts(session, request.prompt_versions)
    except FileNotFoundError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error


@router.get("/case2/metrics", response_model=MetricsResponse)
def get_case2_metrics(session: SessionDep, _: Analyst) -> dict:
    return case2.latest_metrics(session)


@router.patch(
    "/case2/predictions/{prediction_id}/human-review",
    response_model=ComplaintPredictionResponse,
)
def review_case2_prediction(
    prediction_id: str,
    review: Case2ReviewRequest,
    session: SessionDep,
    reviewer: Reviewer,
) -> dict:
    _validate_demo_review(review)
    prediction = case2.review_prediction(session, prediction_id, review, reviewer.object_id)
    if not prediction:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Prediccion no encontrada")
    return case2.serialize_prediction(prediction)
