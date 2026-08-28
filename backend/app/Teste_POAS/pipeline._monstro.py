import json, sys
from pathlib import Path
from ocr import processar_pdf
from IA_extract import extrair_json_de_md
# from seed_script import executar_seed

DOCS_DIR = Path("docs")
MANIFEST_PATH = DOCS_DIR / ".manifest.json"

def main():
    forcar = "--forcar" in sys.argv
    manifest = json.loads(MANIFEST_PATH.read_text("utf-8")) if MANIFEST_PATH.exists() else {}

    for pdf in sorted(DOCS_DIR.glob("*.pdf")):
        if not forcar and manifest.get(pdf.name) == "concluido":
            print(f"[SKIP] '{pdf.name}' já processado.")
            continue

        try:
            print(f"\n=== Processando {pdf.name} ===")
            md_path = processar_pdf(pdf)
            json_path = extrair_json_de_md(md_path)

            input(f"[PAUSA] Revise {json_path}. Pressione Enter para continuar ou Ctrl+C para abortar...")
            # executar_seed(json_path)

            manifest[pdf.name] = "concluido"
        except Exception as e:
            print(f"[ERRO] Falha ao processar '{pdf.name}': {e}")
            manifest[pdf.name] = "erro"
        
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()