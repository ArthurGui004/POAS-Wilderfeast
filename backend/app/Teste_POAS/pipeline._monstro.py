"""
Orquestrador do pipeline: PDF (docs/) -> [1 IA local: OCR + JSON] -> banco.

Roda as 2 etapas em sequência pra cada PDF em docs/ que ainda não foi
processado (controla isso com um arquivo .manifest.json na própria
pasta docs, pra não reprocessar à toa).

Uso:
    python run_pipeline.py
    (processa todos os PDFs novos de docs/)

    python run_pipeline.py --forcar
    (reprocessa mesmo os já feitos)
"""

import json
import subprocess
import sys
from pathlib import Path

DOCS_DIR = Path("docs")
MANIFEST_PATH = DOCS_DIR / ".manifest.json"


def carregar_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def salvar_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def rodar(comando: list[str]) -> None:
    print(f"$ {' '.join(comando)}")
    subprocess.run(comando, check=True)


def main() -> None:
    forcar = "--forcar" in sys.argv
    manifest = carregar_manifest()

    pdfs = sorted(DOCS_DIR.glob("*.pdf"))
    if not pdfs:
        print("Nenhum PDF encontrado em docs/.")
        return

    for pdf in pdfs:
        if not forcar and manifest.get(pdf.name) == "concluido":
            print(f"[SKIP] '{pdf.name}' já processado. Use --forcar pra refazer.")
            continue

        print(f"\n=== Processando {pdf.name} ===")
        try:
            rodar([sys.executable, "1_ocr_extract.py", str(pdf)])

            json_path = Path("seeds/monstros") / f"{pdf.stem}.json"
            print(
                f"[PAUSA] Revise {json_path} antes de continuar. "
                f"Pressione Enter pra confirmar e inserir no banco, ou Ctrl+C pra abortar."
            )
            input()

            rodar([sys.executable, "2_seed_monstro.py", str(json_path)])

            manifest[pdf.name] = "concluido"
            salvar_manifest(manifest)

        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao processar '{pdf.name}': {e}")
            manifest[pdf.name] = "erro"
            salvar_manifest(manifest)


if __name__ == "__main__":
    main()