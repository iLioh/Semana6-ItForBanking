"""Empaqueta solo codigo y frontend compilado; nunca incluye datos RAW ni .env."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "lab06-azure-app.zip"
INCLUDED = (ROOT / "src", ROOT / "prompts", ROOT / "frontend" / "dist")
OFFICIAL_FILES = tuple(ROOT / "data" / "official" / path for path in (
    "case1/empresas_simuladas.csv", "case1/referencia_academica.csv",
    "case2/quejas_bancarias_30.csv", "case2/golden_humano_30.csv",
))


def main() -> None:
    for directory in INCLUDED:
        if not directory.is_dir():
            raise FileNotFoundError(f"Falta directorio de despliegue: {directory}")
    for file in OFFICIAL_FILES:
        if not file.is_file():
            raise FileNotFoundError(f"Falta dataset oficial: {file}")
    if not (ROOT / "requirements.txt").is_file():
        raise FileNotFoundError("Falta requirements.txt")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(ROOT / "requirements.txt", "requirements.txt")
        for file in OFFICIAL_FILES:
            archive.write(file, file.relative_to(ROOT).as_posix())
        for directory in INCLUDED:
            for file in directory.rglob("*"):
                if not file.is_file() or "__pycache__" in file.parts or file.suffix == ".pyc":
                    continue
                archive.write(file, file.relative_to(ROOT).as_posix())
    with ZipFile(OUTPUT) as archive:
        names = archive.namelist()
    forbidden = ("data/peru/", "data/samples/", ".env", ".venv/", "node_modules/")
    allowed_data = {file.relative_to(ROOT).as_posix() for file in OFFICIAL_FILES}
    if any(any(name.startswith(prefix) for prefix in forbidden)
           or (name.startswith("data/") and name not in allowed_data) for name in names):
        OUTPUT.unlink()
        raise RuntimeError("El paquete contiene un archivo de datos o secreto prohibido")
    print(f"Paquete Azure: {OUTPUT} ({len(names)} archivos, {OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
