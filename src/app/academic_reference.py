"""Reglas académicas independientes de la inferencia IA."""

from __future__ import annotations

from typing import Any


def academic_reference_kyc(company: dict[str, Any]) -> str:
    if (
        company["coincidencia_lista_restrictiva"] == "SI"
        or company["beneficiario_final_identificado"] == "NO"
        or company["origen_fondos"] == "NO_DECLARADO"
        or company["actividad_coherente"] == "NO"
    ):
        return "RECHAZADO"
    if (
        company["documentacion_legal"] == "INCOMPLETA"
        or company["pep_relacionado"] == "SI"
        or company["origen_fondos"] == "PARCIAL"
    ):
        return "OBSERVADO"
    return "APROBADO"


def academic_reference_score(company: dict[str, Any]) -> tuple[int, str, str]:
    liquidity = float(company["liquidez"])
    debt = float(company["endeudamiento"])
    points = (
        25 if liquidity >= 1.5 else 15 if liquidity >= 1 else 5,
        25 if debt <= 0.5 else 15 if debt <= 0.7 else 5,
        {"POSITIVO": 25, "VARIABLE": 15, "NEGATIVO": 5}[company["flujo"]],
        {"BUENO": 25, "REGULAR": 15, "MALO": 5}[company["historial_crediticio"]],
    )
    score = sum(points)
    if score >= 80:
        return score, "BAJO", "APROBAR"
    if score >= 50:
        return score, "MEDIO", "EVALUAR"
    return score, "ALTO", "RECHAZAR"
