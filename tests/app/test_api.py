import json

from fastapi.testclient import TestClient

from src.app import case1
from src.app.academic_reference import academic_reference_kyc, academic_reference_score
from src.app.ai import MockAIProvider, ScoringResult
from src.app.official_data import load_companies, load_complaints, load_golden


def test_official_datasets_and_reference() -> None:
    companies = load_companies()
    assert len(companies) == 15
    expected = {
        "AgroPerú SAC": (100, "BAJO", "APROBAR"),
        "TechNova SRL": (60, "MEDIO", "EVALUAR"),
        "Minera Andina": (20, "ALTO", "RECHAZAR"),
        "Constructora Andina SAC": (30, "ALTO", "RECHAZAR"),
    }
    assert {row["empresa"]: academic_reference_score(row) for row in companies
            if row["empresa"] in expected} == expected
    assert academic_reference_kyc(companies[0]) == "APROBADO"
    assert academic_reference_kyc(companies[1]) == "OBSERVADO"
    assert len(load_complaints()) == len(load_golden()) == 30


def test_case1_three_prompts_and_review_persistence(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/case1/run" in paths
    assert "/api/v1/case1/reactiva/run" not in paths
    assert len(client.get("/api/v1/case1/companies").json()) == 15
    response = client.post("/api/v1/case1/run", json={"company_id": "EMPRESA_002"})
    assert response.status_code == 201
    assert response.json()["processed"] == 1
    item = client.get("/api/v1/case1/results").json()["items"][0]
    assert (item["score"], item["recommendation"], item["reference_score"]) == (60, "EVALUAR", 60)
    assert item["kyc"]["status"] == "OBSERVADO"
    assert item["xai"]["requires_human_review"]
    assert item["prompt_versions"] == {
        "kyc": "kyc_v1", "scoring": "scoring_v1", "explainability": "explainability_v1"
    }
    reviewed = client.patch(f"/api/v1/case1/results/{item['id']}/human-review", json={
        "human_decision": "RECHAZAR", "comment": "Revision humana completada."
    })
    assert reviewed.status_code == 200
    reread = client.get(f"/api/v1/case1/results/{item['id']}").json()
    assert (reread["recommendation"], reread["human_decision"], reread["review_status"]) == (
        "EVALUAR", "RECHAZAR", "REVISADA"
    )
    assert '"ruc"' not in json.dumps(reread).lower()


def test_case1_discrepancy_does_not_replace_ai_score(client: TestClient, monkeypatch) -> None:
    class WrongScore(MockAIProvider):
        def generate(self, prompt, response_model, context):
            result = super().generate(prompt, response_model, context)
            if response_model is ScoringResult:
                return result.model_copy(update={"score": 99})
            return result

    monkeypatch.setattr(case1, "get_ai_provider", WrongScore)
    assert client.post("/api/v1/case1/run", json={"company_id": "EMPRESA_002"}).status_code == 201
    item = client.get("/api/v1/case1/results").json()["items"][0]
    assert item["score"] == 99
    assert item["reference_score"] == 60
    assert item["scoring_discrepancy"]
    assert item["requires_human_review"]


def test_case1_runs_all_15_with_mock(client: TestClient) -> None:
    response = client.post("/api/v1/case1/run", json={})
    assert response.status_code == 201
    assert response.json()["processed"] == 15
    assert client.get("/api/v1/case1/results").json()["total"] == 15


def test_case2_separation_golden_metrics_response_review(client: TestClient, monkeypatch) -> None:
    from src.app import case2

    captured = []

    class CapturingProvider(MockAIProvider):
        def generate(self, prompt, response_model, context):
            captured.append((prompt, context.copy()))
            return super().generate(prompt, response_model, context)

    monkeypatch.setattr(case2, "get_ai_provider", CapturingProvider)
    listed = client.get("/api/v1/case2/cases")
    assert listed.status_code == 200
    assert len(listed.json()) == 30
    assert all(row["id"].startswith("QUEJA_") for row in listed.json())
    assert "golden" not in json.dumps(listed.json()).lower()
    classified = client.post("/api/v1/case2/classify", json={
        "case_id": "QUEJA_001", "prompt_version": "classification_v2"
    })
    assert classified.status_code == 201
    body = classified.json()
    assert body["category"] == "FRAUDE"
    assert body["requires_human_review"] is True
    assert body["response_prompt_version"] == "response_v1"
    assert body["draft_response"]
    reviewed = client.patch(f"/api/v1/case2/predictions/{body['id']}/human-review", json={
        "decision": "CORREGIR", "human_category_correction": "SERVICIO",
        "comment": "Revision humana completada."
    })
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "REVISADA"
    assert reviewed.json()["human_category_correction"] == "SERVICIO"
    result = client.post("/api/v1/case2/evaluate", json={
        "prompt_versions": ["classification_v1", "classification_v2"]
    })
    assert result.status_code == 200
    evaluations = result.json()["evaluations"]
    assert len(evaluations) == 2
    assert all(item["provider"] == "mock" for item in evaluations)
    assert set(evaluations[0]["per_class"]) == {"FRAUDE", "SERVICIO", "PRODUCTO"}
    assert len(evaluations[0]["confusion_matrix"]) == 3
    assert "precision_macro" in evaluations[0]
    assert all(item["dataset"] == "official-simulated-30" for item in evaluations)
    assert evaluations[0]["errors"]
    assert {"case_id", "text", "difficulty", "category_golden", "category_predicted",
            "prompt_version", "confidence", "rationale", "secondary_category",
            "ambiguity_detected"} <= set(evaluations[0]["errors"][0])
    assert len(captured) == 6  # 1 clasificación + 1 respuesta + 4 lotes de evaluación
    for prompt, context in captured:
        payload = json.dumps(context, ensure_ascii=False).lower()
        assert "categoria_golden" not in payload
        assert "prioridad_golden" not in payload
        assert "justificacion_golden" not in payload
        assert "golden" not in prompt.lower()


def test_validation_error_is_safe(client: TestClient) -> None:
    response = client.post("/api/v1/case2/classify", json={"text": "Juan Pérez"})
    assert response.status_code == 422
    assert response.json()["correlation_id"]
    assert "Juan Pérez" not in json.dumps(response.json())
