"""Caso 1 oficial: KYC IA, scoring IA, referencia independiente y XAI."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from src.app.academic_reference import academic_reference_kyc, academic_reference_score
from src.app.ai import (
    ExplainabilityResult,
    KYCResult,
    ScoringResult,
    get_ai_provider,
    load_prompt,
    timed_generate,
)
from src.app.models import (
    CompanyProcessed,
    FinancialAssessment,
    HumanReview,
    ModelRun,
    ProcessingBatch,
)
from src.app.official_data import load_case1_reference, load_companies
from src.app.schemas import Case1ReviewRequest

VERSIONS = {"kyc": "kyc_v1", "scoring": "scoring_v1", "explainability": "explainability_v1"}
FINANCIAL_KEYS = ("liquidez", "endeudamiento", "flujo", "historial_crediticio")


def list_companies() -> list[dict[str, str]]:
    return [{"id": row["empresa_id"], "name": row["empresa"], "sector": row["sector"]}
            for row in load_companies()]


def _run_prompt(provider, batch: ProcessingBatch, session: Session, stage: str, model,
                context, company_id: str):
    version = VERSIONS[stage]
    result, latency = timed_generate(provider, load_prompt("case1", f"{version}.txt"), model, context)
    session.add(ModelRun(
        batch_id=batch.id, case_type="CASE1_OFFICIAL", prompt_version=version,
        model=provider.model, provider=provider.name, latency_ms=latency,
        success=True, result_summary={"company_id": company_id, "stage": stage},
    ))
    return result


def run_official_cases(session: Session, company_id: str | None = None) -> tuple[str, int]:
    companies = load_companies()
    references = load_case1_reference()
    if set(references) != {row["empresa_id"] for row in companies}:
        raise ValueError("La referencia académica no corresponde a las 15 empresas")
    selected = [row for row in companies if company_id is None or row["empresa_id"] == company_id]
    if not selected:
        raise ValueError("Empresa simulada no encontrada")
    provider = get_ai_provider()
    batch = ProcessingBatch(case_type="CASE1_OFFICIAL", source="Dataset definitivo simulado")
    session.add(batch)
    session.flush()
    try:
        for row in selected:
            financials = {key: row[key] for key in FINANCIAL_KEYS}
            kyc_input = {key: row[key] for key in (
                "empresa", "sector", "pais", "documentacion_legal",
                "beneficiario_final_identificado", "origen_fondos", "actividad_coherente",
                "coincidencia_lista_restrictiva", "pep_relacionado",
            )}
            kyc = _run_prompt(provider, batch, session, "kyc", KYCResult,
                              {"company": kyc_input}, row["empresa_id"])
            scoring = _run_prompt(provider, batch, session, "scoring", ScoringResult,
                                  {"financials": financials}, row["empresa_id"])
            reference_score, reference_risk, reference_recommendation = academic_reference_score(row)
            reference_kyc = academic_reference_kyc(row)
            source_reference = references[row["empresa_id"]]
            if (
                int(source_reference["score_referencia"]) != reference_score
                or source_reference["riesgo_referencia"] != reference_risk
                or source_reference["recomendacion_referencia"] != reference_recommendation
                or source_reference["kyc_golden"] != reference_kyc
            ):
                raise ValueError(f"Referencia académica inconsistente: {row['empresa_id']}")
            discrepancy = scoring.score != reference_score or (
                scoring.risk_level, scoring.recommendation
            ) != (reference_risk, reference_recommendation)
            xai = _run_prompt(provider, batch, session, "explainability", ExplainabilityResult, {
                "kyc": kyc.model_dump(), "scoring": scoring.model_dump(),
                "financials": financials, "scoring_discrepancy": discrepancy,
            }, row["empresa_id"])
            company = CompanyProcessed(
                batch_id=batch.id, anonymous_code=row["empresa_id"],
                public_data={"name": row["empresa"], "sector": row["sector"],
                             "region": row["region"], "country": row["pais"]},
                provenance={"dataset": "SIMULADO_OFICIAL"},
            )
            company.assessments.append(FinancialAssessment(
                synthetic_data=financials, score=scoring.score,
                risk_level=scoring.risk_level, recommendation=scoring.recommendation,
                factors=scoring.calculation_breakdown, explanation=xai.explanation,
                prompt_version=VERSIONS["scoring"], prompt_versions=VERSIONS,
                kyc_result=kyc.model_dump(), scoring_result=scoring.model_dump(),
                xai_result=xai.model_dump(), reference_score=reference_score,
                scoring_discrepancy=discrepancy, kyc_reference=reference_kyc,
                kyc_discrepancy=kyc.status != reference_kyc, model=provider.model,
            ))
            session.add(company)
        batch.status = "COMPLETED"
        batch.completed_at = datetime.now(UTC)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return batch.id, len(selected)


def serialize_assessment(assessment: FinancialAssessment) -> dict:
    return {
        "id": assessment.id, "batch_id": assessment.company.batch_id,
        "company_code": assessment.company.anonymous_code,
        "company_name": assessment.company.public_data.get("name", ""),
        "public_variables": assessment.company.public_data,
        "synthetic_variables": assessment.synthetic_data,
        "kyc": assessment.kyc_result, "scoring": assessment.scoring_result,
        "xai": assessment.xai_result, "reference_score": assessment.reference_score,
        "scoring_discrepancy": assessment.scoring_discrepancy,
        "requires_human_review": (
            assessment.scoring_discrepancy or assessment.kyc_discrepancy
            or assessment.scoring_result.get("requires_human_review", False)
            or assessment.kyc_result.get("requires_human_review", False)
            or assessment.xai_result.get("requires_human_review", False)
        ),
        "kyc_reference": assessment.kyc_reference,
        "kyc_discrepancy": assessment.kyc_discrepancy,
        "score": assessment.score, "risk_level": assessment.risk_level,
        "recommendation": assessment.recommendation,
        "prompt_versions": assessment.prompt_versions, "model": assessment.model,
        "executed_at": assessment.executed_at,
        "review_status": assessment.review_status,
        "human_decision": assessment.human_decision,
        "analyst_comment": assessment.analyst_comment,
    }


def list_assessments(session: Session, page: int, page_size: int, risk_level: str | None,
                     review_status: str | None) -> tuple[list[dict], int]:
    filters = []
    if risk_level:
        filters.append(FinancialAssessment.risk_level == risk_level)
    if review_status:
        filters.append(FinancialAssessment.review_status == review_status)
    total = session.scalar(select(func.count()).select_from(FinancialAssessment).where(*filters)) or 0
    statement = (select(FinancialAssessment).options(joinedload(FinancialAssessment.company))
                 .where(*filters).order_by(FinancialAssessment.executed_at.desc())
                 .offset((page - 1) * page_size).limit(page_size))
    return [serialize_assessment(item) for item in session.scalars(statement)], total


def get_assessment(session: Session, assessment_id: str) -> dict | None:
    assessment = session.scalar(select(FinancialAssessment)
                                .options(joinedload(FinancialAssessment.company))
                                .where(FinancialAssessment.id == assessment_id))
    return serialize_assessment(assessment) if assessment else None


def review_assessment(session: Session, assessment_id: str, review: Case1ReviewRequest,
                      reviewer: str) -> dict | None:
    assessment = session.get(FinancialAssessment, assessment_id)
    if not assessment:
        return None
    assessment.review_status = "REVISADA"
    assessment.human_decision = review.human_decision
    assessment.analyst_comment = review.comment
    session.add(HumanReview(
        resource_type="FINANCIAL_ASSESSMENT", resource_id=assessment.id,
        reviewer_object_id=reviewer, decision=review.human_decision, comment=review.comment,
    ))
    session.commit()
    return get_assessment(session, assessment_id)
