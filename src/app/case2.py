"""Caso 2 oficial: clasificación, evaluación golden y respuesta separada."""

from __future__ import annotations

from datetime import UTC, datetime

from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.ai import (
    ComplaintBatchAIResult,
    ComplaintClassification,
    ResponseDraft,
    get_ai_provider,
    load_prompt,
    timed_generate,
)
from src.app.models import Complaint, ComplaintPrediction, HumanReview, ModelRun
from src.app.official_data import load_complaints, load_golden
from src.app.schemas import Case2ReviewRequest

CATEGORIES = ("FRAUDE", "SERVICIO", "PRODUCTO")
VERSIONS = ("classification_v1", "classification_v2")


def _input_text(row: dict[str, str]) -> str:
    return f"{row['asunto']}. {row['cuerpo']}"


def list_prepared_cases() -> list[dict[str, str]]:
    return [{"id": row["caso_id"], "text": _input_text(row), "difficulty": row["dificultad"]}
            for row in load_complaints()]


def _predict(provider, text: str, version: str):
    if version not in VERSIONS:
        raise ValueError("Versión de prompt no permitida")
    # Solo texto de entrada: ningún dato de load_golden entra al proveedor IA.
    result, latency = timed_generate(
        provider, load_prompt("case2", f"{version}.txt"),
        ComplaintClassification, {"text": text},
    )
    if result.category == "FRAUDE" and not result.requires_human_review:
        result = result.model_copy(update={"requires_human_review": True})
    return result, latency


def _predict_batch(provider, rows: list[dict[str, str]], version: str):
    canonical = load_prompt("case2", f"{version}.txt")
    rules = canonical.partition("Devuelve SOLO JSON")[0].replace(
        "{{text}}", "cada texto del arreglo de casos"
    )
    prompt = (
        rules + "\nClasifica cada caso por separado. Conserva exactamente cada case_id. "
        "Devuelve SOLO JSON con items: una lista de objetos con case_id y todos los campos "
        "de ComplaintClassification para cada caso, sin omitir ni duplicar IDs. "
        "Casos: {{cases}}"
    )
    cases = [{"case_id": row["caso_id"], "text": _input_text(row)} for row in rows]
    batch, latency = timed_generate(provider, prompt, ComplaintBatchAIResult, {"cases": cases})
    by_id = {item.case_id: item for item in batch.items}
    if len(batch.items) != len(rows) or set(by_id) != {row["caso_id"] for row in rows}:
        raise ValueError("La respuesta IA omite o duplica IDs del lote")
    return {
        case_id: item.model_copy(update={"requires_human_review": True})
        if item.category == "FRAUDE" and not item.requires_human_review else item
        for case_id, item in by_id.items()
    }, latency


def classify_prepared_case(session: Session, case_id: str,
                           prompt_version: str) -> ComplaintPrediction:
    row = next((item for item in load_complaints() if item["caso_id"] == case_id), None)
    if row is None:
        raise ValueError("Código de queja simulada no encontrado")
    provider = get_ai_provider()
    text = _input_text(row)
    result, latency = _predict(provider, text, prompt_version)
    draft, response_latency = timed_generate(
        provider, load_prompt("case2", "response_v1.txt"), ResponseDraft,
        {"text": text, "category": result.category, "summary": result.summary},
    )
    prediction = ComplaintPrediction(
        case_id=case_id, anonymized_text=text, category=result.category,
        confidence=result.confidence, priority=result.priority, summary=result.summary,
        rationale=result.rationale, secondary_category=result.secondary_category,
        ambiguity_detected=result.ambiguity_detected,
        requires_human_review=result.requires_human_review,
        draft_response=draft.draft_response, prompt_version=prompt_version,
        response_prompt_version="response_v1", model=provider.model,
        latency_ms=latency + response_latency,
    )
    session.add(prediction)
    for version, spent in ((prompt_version, latency), ("response_v1", response_latency)):
        session.add(ModelRun(
            case_type="CASE2", prompt_version=version, model=provider.model,
            provider=provider.name, latency_ms=spent, success=True,
            result_summary={"case_id": case_id, "category": result.category},
        ))
    session.commit()
    session.refresh(prediction)
    return prediction


def serialize_prediction(prediction: ComplaintPrediction) -> dict:
    return {
        "id": prediction.id, "case_id": prediction.case_id,
        "category": prediction.category, "confidence": prediction.confidence,
        "priority": prediction.priority, "summary": prediction.summary,
        "rationale": prediction.rationale,
        "secondary_category": prediction.secondary_category,
        "ambiguity_detected": prediction.ambiguity_detected,
        "requires_human_review": prediction.requires_human_review,
        "draft_response": prediction.draft_response,
        "prompt_version": prediction.prompt_version,
        "response_prompt_version": prediction.response_prompt_version,
        "model": prediction.model, "latency_ms": prediction.latency_ms,
        "executed_at": prediction.executed_at,
        "review_status": prediction.review_status,
        "analyst_decision": prediction.analyst_decision,
        "human_category_correction": prediction.human_category_correction,
        "analyst_comment": prediction.analyst_comment,
    }


def calculate_metrics(version: str, rows: list[dict], predictions: dict[str, ComplaintClassification],
                      golden: dict[str, dict[str, str]], provider) -> dict:
    truth = [golden[row["caso_id"]]["categoria_golden"] for row in rows]
    predicted = [predictions[row["caso_id"]].category for row in rows]
    precision, recall, f1, support = precision_recall_fscore_support(
        truth, predicted, labels=CATEGORIES, zero_division=0
    )
    matrix = confusion_matrix(truth, predicted, labels=CATEGORIES)
    errors = [{
        "case_id": row["caso_id"], "text": _input_text(row),
        "difficulty": row["dificultad"], "category_golden": golden[row["caso_id"]]["categoria_golden"],
        "category_predicted": predictions[row["caso_id"]].category,
        "prompt_version": version, "confidence": predictions[row["caso_id"]].confidence,
        "rationale": predictions[row["caso_id"]].rationale,
        "secondary_category": predictions[row["caso_id"]].secondary_category,
        "ambiguity_detected": predictions[row["caso_id"]].ambiguity_detected,
    } for row in rows if golden[row["caso_id"]]["categoria_golden"] != predictions[row["caso_id"]].category]
    return {
        "prompt_version": version, "provider": provider.name, "model": provider.model,
        "dataset": "official-simulated-30", "accuracy": round(float(accuracy_score(truth, predicted)), 4),
        "per_class": {category: {
            "precision": round(float(precision[i]), 4), "recall": round(float(recall[i]), 4),
            "f1": round(float(f1[i]), 4), "support": int(support[i]),
        } for i, category in enumerate(CATEGORIES)},
        "precision_macro": round(float(precision.mean()), 4),
        "recall_macro": round(float(recall.mean()), 4),
        "f1_macro": round(float(f1.mean()), 4),
        "confusion_matrix": {
            expected: {actual: int(matrix[i][j]) for j, actual in enumerate(CATEGORIES)}
            for i, expected in enumerate(CATEGORIES)
        },
        "errors": errors,
    }


def evaluate_prompts(session: Session, versions: list[str]) -> dict:
    if len(versions) != 2 or set(versions) != set(VERSIONS):
        raise ValueError("Se requieren classification_v1 y classification_v2")
    rows = load_complaints()
    provider = get_ai_provider()
    predictions_by_version: dict[str, dict[str, ComplaintClassification]] = {}
    latencies: dict[str, float] = {}
    # Se completa toda la inferencia ANTES de abrir el golden humano.
    for version in versions:
        predictions_by_version[version] = {}
        latencies[version] = 0.0
        for offset in range(0, len(rows), 15):
            batch_results, latency = _predict_batch(provider, rows[offset:offset + 15], version)
            predictions_by_version[version].update(batch_results)
            latencies[version] += latency
    golden = load_golden()
    if set(golden) != {row["caso_id"] for row in rows}:
        raise ValueError("IDs de quejas y golden humano no coinciden")
    evaluations = []
    try:
        for version in versions:
            predictions = predictions_by_version[version]
            for row in rows:
                case_id = row["caso_id"]
                complaint = session.scalar(select(Complaint).where(Complaint.source_code == case_id))
                if complaint is None:
                    complaint = Complaint(
                        source_code=case_id, anonymized_text=_input_text(row),
                        golden_label=golden[case_id]["categoria_golden"],
                        difficulty=row["dificultad"], provenance="SIMULADO_OFICIAL",
                    )
                    session.add(complaint)
                    session.flush()
                result = predictions[case_id]
                session.add(ComplaintPrediction(
                    complaint_id=complaint.id, case_id=case_id,
                    anonymized_text=_input_text(row), category=result.category,
                    confidence=result.confidence, priority=result.priority,
                    summary=result.summary, rationale=result.rationale,
                    secondary_category=result.secondary_category,
                    ambiguity_detected=result.ambiguity_detected,
                    requires_human_review=result.requires_human_review,
                    draft_response="", prompt_version=version, model=provider.model,
                    latency_ms=round(latencies[version] / len(rows), 3),
                ))
            metrics = calculate_metrics(version, rows, predictions, golden, provider)
            evaluations.append(metrics)
            session.add(ModelRun(
                case_type="CASE2_OFFICIAL_EVALUATION", prompt_version=version,
                model=provider.model, provider=provider.name,
                latency_ms=round(latencies[version], 3), success=True,
                result_summary=metrics,
            ))
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"evaluations": evaluations, "generated_at": datetime.now(UTC)}


def latest_metrics(session: Session) -> dict:
    runs = session.scalars(select(ModelRun)
                           .where(ModelRun.case_type == "CASE2_OFFICIAL_EVALUATION")
                           .order_by(ModelRun.executed_at.desc()).limit(2)).all()
    return {
        "evaluations": [run.result_summary for run in reversed(runs)],
        "generated_at": max((run.executed_at for run in runs), default=datetime.now(UTC)),
    }


def review_prediction(session: Session, prediction_id: str, review: Case2ReviewRequest,
                      reviewer: str) -> ComplaintPrediction | None:
    prediction = session.get(ComplaintPrediction, prediction_id)
    if prediction is None:
        return None
    prediction.review_status = "REVISADA"
    prediction.analyst_decision = review.decision
    prediction.human_category_correction = review.human_category_correction
    prediction.analyst_comment = review.comment
    session.add(HumanReview(
        resource_type="COMPLAINT_PREDICTION", resource_id=prediction.id,
        reviewer_object_id=reviewer, decision=review.decision, comment=review.comment,
    ))
    session.commit()
    session.refresh(prediction)
    return prediction
