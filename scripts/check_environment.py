"""Verifica el entorno local, los datasets y, opcionalmente, Azure OpenAI."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

PACKAGES = (
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "scikit-learn",
    "openai",
    "python-dotenv",
    "pydantic",
    "tenacity",
    "jupyterlab",
    "ipykernel",
)

VERSIONED_DATASETS = {
    PROJECT_ROOT / "data/official/case1/empresas_simuladas.csv": {
        "empresa_id", "empresa", "sector", "liquidez", "endeudamiento", "flujo",
        "historial_crediticio", "documentacion_legal",
    },
    PROJECT_ROOT / "data/official/case1/referencia_academica.csv": {
        "empresa_id", "score_referencia", "kyc_golden",
    },
    PROJECT_ROOT / "data/official/case2/quejas_bancarias_30.csv": {
        "caso_id", "asunto", "cuerpo", "dificultad",
    },
    PROJECT_ROOT / "data/official/case2/golden_humano_30.csv": {
        "caso_id", "categoria_golden", "prioridad_golden",
    },
}


def normalize_column(column: str) -> str:
    """Normaliza tildes para comparar encabezados sin modificar el dataset."""

    translation = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return column.translate(translation)


def check_python() -> bool:
    current = sys.version_info
    valid = current.major == 3 and current.minor == 12
    state = "OK" if valid else "ERROR"
    print(f"[{state}] Python {current.major}.{current.minor}.{current.micro}")
    if not valid:
        print("        Ejecute el script con: uv run python scripts/check_environment.py")
    return valid


def check_packages() -> bool:
    valid = True
    for package in PACKAGES:
        try:
            installed_version = version(package)
            print(f"[OK] {package} {installed_version}")
        except PackageNotFoundError:
            valid = False
            print(f"[ERROR] No se encontro el paquete {package}")
    return valid


def _check_dataset_group(datasets: dict[Path, set[str]], required: bool) -> bool:
    valid = True
    for path, required_columns in datasets.items():
        relative_path = path.relative_to(PROJECT_ROOT)
        if not path.is_file():
            if required:
                valid = False
                print(f"[ERROR] No existe {relative_path}")
            else:
                print(f"[INFO] RAW privado no disponible localmente: {relative_path}")
            continue

        try:
            sample = pd.read_csv(path, nrows=5)
        except (OSError, UnicodeDecodeError, pd.errors.ParserError) as error:
            valid = False
            print(f"[ERROR] No se pudo leer {relative_path}: {error}")
            continue

        normalized_columns = {normalize_column(column) for column in sample.columns}
        missing = sorted(required_columns - normalized_columns)
        if missing:
            valid = False
            print(f"[ERROR] {relative_path} no contiene: {', '.join(missing)}")
            continue

        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"[OK] {relative_path} ({size_mb:.1f} MB, {len(sample.columns)} columnas)")

    return valid


def check_datasets() -> bool:
    """Valida exclusivamente los cuatro CSV oficiales simulados."""

    if not _check_dataset_group(VERSIONED_DATASETS, required=True):
        return False
    try:
        from scripts.seed_official_datasets import validate_official_datasets

        validate_official_datasets()
    except (OSError, ValueError) as error:
        print(f"[ERROR] Datasets oficiales inválidos: {error}")
        return False
    return True


def check_azure() -> bool:
    from openai import OpenAIError
    from pydantic import ValidationError

    from src.azure_client import test_azure_connection
    from src.config import load_azure_settings

    try:
        settings = load_azure_settings()
        print(
            "[OK] Configuracion Azure: "
            f"host={settings.endpoint.host}, deployment={settings.deployment}, "
            f"api_version={settings.api_version}"
        )
        response = test_azure_connection()
    except (OpenAIError, ValidationError, ValueError) as error:
        print(f"[ERROR] Fallo la verificacion de Azure OpenAI: {error}")
        return False

    state = "OK" if response.strip().upper() == "OK" else "ADVERTENCIA"
    print(f"[{state}] Azure OpenAI respondio: {response.strip()!r}")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--azure",
        action="store_true",
        help="realiza una solicitud minima a Azure OpenAI",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("Verificacion del Laboratorio 06\n")

    checks = [check_python(), check_packages(), check_datasets()]
    if args.azure:
        checks.append(check_azure())
    else:
        print("[INFO] Azure OpenAI no fue consultado; use --azure para verificarlo.")

    if all(checks):
        print("\nEntorno preparado correctamente.")
        return 0

    print("\nLa verificacion encontro errores.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
