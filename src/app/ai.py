"""Proveedor IA real y fake local con contratos estructurados compartidos."""

from __future__ import annotations

import json
import time
from typing import Any, Literal, Protocol, TypeVar

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI
from pydantic import BaseModel, Field

from src.app.config import PROJECT_ROOT, AppSettings, get_settings

T = TypeVar("T", bound=BaseModel)
PROMPT_ROOT = PROJECT_ROOT / "prompts"


class KYCResult(BaseModel):
    status: Literal["APROBADO", "OBSERVADO", "RECHAZADO"]
    justification: str
    detected_risks: list[str]
    missing_or_pending_information: list[str]
    requires_human_review: bool
    confidence: Literal["BAJA", "MEDIA", "ALTA"]


class ScoringResult(BaseModel):
    score: int = Field(ge=0, le=100)
    risk_level: Literal["BAJO", "MEDIO", "ALTO"]
    recommendation: Literal["APROBAR", "EVALUAR", "RECHAZAR"]
    payment_capacity_analysis: str
    detected_risks: list[str]
    calculation_breakdown: list[str]
    requires_human_review: bool


class ExplainabilityResult(BaseModel):
    explanation: str
    key_variables: list[str]
    possible_biases: list[str]
    limitations: list[str]
    transparency_assessment: str
    confidence: Literal["BAJA", "MEDIA", "ALTA"]
    requires_human_review: bool


class ComplaintClassification(BaseModel):
    category: Literal["FRAUDE", "SERVICIO", "PRODUCTO"]
    confidence: Literal["BAJA", "MEDIA", "ALTA"]
    priority: Literal["BAJA", "MEDIA", "ALTA"]
    summary: str
    rationale: str
    secondary_category: Literal["FRAUDE", "SERVICIO", "PRODUCTO", "NINGUNA"]
    ambiguity_detected: bool
    requires_human_review: bool


class ComplaintBatchItem(ComplaintClassification):
    case_id: str


class ComplaintBatchAIResult(BaseModel):
    items: list[ComplaintBatchItem]


class ResponseDraft(BaseModel):
    draft_response: str


class AIProvider(Protocol):
    name: str
    model: str

    def generate(self, prompt: str, response_model: type[T], context: dict[str, Any]) -> T: ...


def load_prompt(area: str, name: str) -> str:
    path = PROMPT_ROOT / area / name
    if not path.is_file():
        raise FileNotFoundError(f"Prompt versionado no encontrado: {path.relative_to(PROJECT_ROOT)}")
    return path.read_text(encoding="utf-8")


class MockAIProvider:
    """Fake determinístico; sus resultados nunca son métricas reales de Azure."""

    name = "mock"
    model = "mock-deterministic-v2"

    def generate(self, prompt: str, response_model: type[T], context: dict[str, Any]) -> T:
        del prompt
        if response_model is KYCResult:
            company = context["company"]
            rejected = any((
                company["coincidencia_lista_restrictiva"] == "SI",
                company["beneficiario_final_identificado"] == "NO",
                company["origen_fondos"] == "NO_DECLARADO",
                company["actividad_coherente"] == "NO",
            ))
            observed = any((
                company["documentacion_legal"] == "INCOMPLETA",
                company["pep_relacionado"] == "SI",
                company["origen_fondos"] == "PARCIAL",
            ))
            status = "RECHAZADO" if rejected else "OBSERVADO" if observed else "APROBADO"
            return response_model.model_validate({
                "status": status, "justification": "Evaluación de datos KYC simulados.",
                "detected_risks": [] if status == "APROBADO" else ["Información KYC por revisar"],
                "missing_or_pending_information": [], "requires_human_review": True,
                "confidence": "ALTA",
            })
        if response_model is ScoringResult:
            values = context["financials"]
            liquidity = float(values["liquidez"])
            debt = float(values["endeudamiento"])
            points = [
                25 if liquidity >= 1.5 else 15 if liquidity >= 1 else 5,
                25 if debt <= 0.5 else 15 if debt <= 0.7 else 5,
                {"POSITIVO": 25, "VARIABLE": 15, "NEGATIVO": 5}[values["flujo"]],
                {"BUENO": 25, "REGULAR": 15, "MALO": 5}[values["historial_crediticio"]],
            ]
            score = sum(points)
            risk, recommendation = (
                ("BAJO", "APROBAR") if score >= 80 else
                ("MEDIO", "EVALUAR") if score >= 50 else ("ALTO", "RECHAZAR")
            )
            return response_model.model_validate({
                "score": score, "risk_level": risk, "recommendation": recommendation,
                "payment_capacity_analysis": "Análisis simulado con cuatro variables financieras.",
                "detected_risks": [] if risk == "BAJO" else ["Capacidad de pago por revisar"],
                "calculation_breakdown": [
                    f"{name}: {point}" for name, point in zip(
                        ("liquidez", "endeudamiento", "flujo", "historial"), points, strict=True
                    )
                ],
                "requires_human_review": True,
            })
        if response_model is ExplainabilityResult:
            return response_model.model_validate({
                "explanation": "El score IA se basa en liquidez, deuda, flujo e historial simulados. "
                "No constituye una decisión crediticia real y requiere revisión humana.",
                "key_variables": list(context["financials"]),
                "possible_biases": ["Datos simulados no representan a empresas reales"],
                "limitations": ["No se verificó información real"],
                "transparency_assessment": "Rúbrica académica explícita; revisar discrepancias.",
                "confidence": "MEDIA", "requires_human_review": True,
            })
        if response_model is ComplaintClassification:
            return response_model.model_validate(self._classify_complaint(context))
        if response_model is ComplaintBatchAIResult:
            return response_model.model_validate({"items": [
                {"case_id": row["case_id"], **self._classify_complaint({"text": row["text"]})}
                for row in context["cases"]
            ]})
        if response_model is ResponseDraft:
            return response_model.model_validate({
                "draft_response": "Gracias por contactarnos. Entendemos su preocupación sobre "
                f"{context['summary']}. Revisaremos la información reportada y le indicaremos "
                "los próximos pasos por los canales oficiales."
            })
        raise TypeError(f"Modelo de respuesta mock no soportado: {response_model.__name__}")

    @staticmethod
    def _classify_complaint(context: dict[str, Any]) -> dict[str, Any]:
        text = context["text"].lower()
        fraud = any(term in text for term in (
            "no reconoc", "no autoric", "no realic", "no hice", "desconozco"
        ))
        product = any(term in text for term in ("tasa", "comisión", "comision", "beneficio"))
        service = any(term in text for term in ("demora", "atención", "atencion", "no proces"))
        category = "FRAUDE" if fraud else "PRODUCTO" if product else "SERVICIO"
        secondary = "SERVICIO" if fraud and service else "PRODUCTO" if fraud and product else "NINGUNA"
        return {
            "category": category,
            "confidence": "ALTA" if fraud or product or service else "BAJA",
            "priority": "ALTA" if fraud else "MEDIA",
            "summary": context["text"][:180],
            "rationale": "Clasificación fake de la preocupación principal; no es resultado real.",
            "secondary_category": secondary,
            "ambiguity_detected": secondary != "NINGUNA",
            "requires_human_review": category == "FRAUDE",
        }


class AzureOpenAIProvider:
    name = "azure"

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.model = settings.azure_openai_deployment
        common = {
            "base_url": f"{settings.azure_openai_endpoint.rstrip('/')}/openai/v1/",
            "timeout": settings.ai_timeout_seconds,
            "max_retries": settings.ai_max_retries,
        }
        if settings.azure_openai_api_key:
            self.client = OpenAI(api_key=settings.azure_openai_api_key, **common)
        else:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://ai.azure.com/.default"
            )
            self.client = OpenAI(api_key=token_provider, **common)

    def generate(self, prompt: str, response_model: type[T], context: dict[str, Any]) -> T:
        rendered = prompt
        for key, value in context.items():
            rendered = rendered.replace("{{" + key + "}}", json.dumps(value, ensure_ascii=False))
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[{"role": "user", "content": rendered}],
            response_format=response_model,
            reasoning_effort="minimal",
            max_completion_tokens=6000 if response_model is ComplaintBatchAIResult else 1200,
        )
        message = response.choices[0].message
        if message.refusal:
            raise ValueError(f"Azure OpenAI rechazó la solicitud: {message.refusal}")
        if message.parsed is None:
            raise ValueError("Azure OpenAI no devolvió una respuesta estructurada")
        return message.parsed


def get_ai_provider(settings: AppSettings | None = None) -> AIProvider:
    resolved = settings or get_settings()
    if resolved.ai_provider == "mock":
        return MockAIProvider()
    return AzureOpenAIProvider(resolved)


def timed_generate[R: BaseModel](
    provider: AIProvider, prompt: str, response_model: type[R], context: dict[str, Any]
) -> tuple[R, float]:
    started = time.perf_counter()
    result = provider.generate(prompt, response_model, context)
    return result, round((time.perf_counter() - started) * 1000, 3)
