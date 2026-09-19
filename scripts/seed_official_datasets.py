"""Valida datasets definitivos; con --apply --yes los carga sin sobrescribir Blob."""

from __future__ import annotations

import argparse
import csv
from collections import Counter

from src.app.config import PROJECT_ROOT, get_settings
from src.app.storage import PrivateBlobStorage

ROOT = PROJECT_ROOT / "data" / "official"
FILES = {
    "case1/empresas_simuladas.csv": {"empresa_id", "empresa", "sector", "documentacion_legal",
                                     "beneficiario_final_identificado", "origen_fondos",
                                     "actividad_coherente", "coincidencia_lista_restrictiva",
                                     "pep_relacionado", "liquidez", "endeudamiento", "flujo",
                                     "historial_crediticio", "es_simulado"},
    "case1/referencia_academica.csv": {"empresa_id", "kyc_golden", "score_referencia",
                                        "riesgo_referencia", "recomendacion_referencia"},
    "case2/quejas_bancarias_30.csv": {"caso_id", "asunto", "cuerpo", "dificultad", "es_simulado"},
    "case2/golden_humano_30.csv": {"caso_id", "categoria_golden", "prioridad_golden",
                                   "justificacion_golden"},
}


def validate_official_datasets() -> dict[str, list[dict[str, str]]]:
    loaded = {}
    for name, required in FILES.items():
        path = ROOT / name
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            missing = required - set(reader.fieldnames or ())
            if missing:
                raise ValueError(f"{name}: faltan columnas {sorted(missing)}")
            loaded[name] = list(reader)
    companies, reference, complaints, golden = loaded.values()
    if len(companies) != 15 or len(reference) != 15:
        raise ValueError("Caso 1 requiere 15 empresas y 15 referencias")
    if len(complaints) != 30 or len(golden) != 30:
        raise ValueError("Caso 2 requiere 30 quejas y 30 etiquetas golden")
    for left, right, key in ((companies, reference, "empresa_id"),
                             (complaints, golden, "caso_id")):
        left_ids, right_ids = [row[key] for row in left], [row[key] for row in right]
        if len(set(left_ids)) != len(left_ids) or len(set(right_ids)) != len(right_ids):
            raise ValueError(f"IDs duplicados: {key}")
        if set(left_ids) != set(right_ids):
            raise ValueError(f"IDs de entrada y referencia no coinciden: {key}")
    if Counter(row["categoria_golden"] for row in golden) != {
        "FRAUDE": 10, "SERVICIO": 10, "PRODUCTO": 10
    }:
        raise ValueError("Golden humano debe ser 10/10/10")
    if any(row["es_simulado"] != "SI" for row in companies + complaints):
        raise ValueError("Solo se permiten entradas simuladas oficiales")
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="cargar a Blob en Fase 2")
    parser.add_argument("--yes", action="store_true", help="confirma carga remota")
    args = parser.parse_args()
    loaded = validate_official_datasets()
    print("Datasets válidos: 15 empresas, 30 quejas, golden humano 10/10/10")
    if not args.apply:
        print("Solo validación local; Azure no consultado")
        return
    if not args.yes:
        parser.error("--apply requiere --yes")
    settings = get_settings()
    if not settings.azure_storage_account_url:
        parser.error("AZURE_STORAGE_ACCOUNT_URL no configurado")
    storage = PrivateBlobStorage(settings)
    for name in loaded:
        created = storage.upload_prepared_if_absent(name, (ROOT / name).read_bytes())
        print(f"{name}: {'cargado' if created else 'ya existe; sin cambios'}")


if __name__ == "__main__":
    main()
