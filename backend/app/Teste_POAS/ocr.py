"""
Percorre todos os PDFs de uma pasta e, usando UM modelo de IA rodando
local (Qwen2-VL-2B-Instruct), extrai o conteúdo de cada um já em JSON
estruturado — sem etapa de texto intermediário.

Uso:
    python ocr.py                      -> processa a pasta padrão (docs/)
    python ocr.py caminho/da/pasta     -> processa uma pasta específica
    python ocr.py --forcar             -> reprocessa mesmo os já feitos

Saída:
    Um arquivo <nome_do_pdf>.json em seeds/monstros/ para cada PDF.
    Um .manifest.json na própria pasta de PDFs, pra não reprocessar
    o que já foi feito (a menos que use --forcar).
"""

import json
import os
import sys
from pathlib import Path

import pymupdf  # PyMuPDF
import torch
from huggingface_hub import login
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from qwen_vl_utils import process_vision_info

MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"
PASTA_PADRAO = Path("docs")
SEEDS_DIR = Path("seeds/monstros")

INSTRUCAO = """\
As imagens a seguir são páginas de um livro de regras de RPG (sistema \
Wilderfeast), descrevendo UM monstro. Leia o conteúdo das imagens e \
responda APENAS com um objeto JSON válido, sem markdown, sem comentário, \
sem texto antes ou depois. Não invente informação que não está nas \
imagens: se um campo não aparecer, use null (para string) ou lista vazia \
(para listas).

Schema exato a seguir:
{
  "nome": string,
  "dieta": string | null,
  "comportamento": string | null,
  "descricao": string | null,
  "habitats": [string],
  "tracos": [string],
  "habilidades": [string]
}
"""

_model = None
_processor = None


def autenticar_hf() -> str | None:
    """Lê o token do Hugging Face da variável de ambiente HF_TOKEN e
    autentica. Se não existir, segue sem token (com limite de taxa menor)."""
    token = "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"
    if token:
        login(token=token)
        print("[IA] Autenticado no Hugging Face com HF_TOKEN.")
    else:
        print("[IA] HF_TOKEN não encontrado no ambiente — baixando sem autenticação.")
    return token


def carregar_modelo():
    """Carrega o modelo uma única vez e reaproveita entre todos os PDFs."""
    global _model, _processor
    if _model is None:
        token = autenticar_hf()
        print(f"[IA] Carregando modelo '{MODEL_NAME}' (pode demorar na primeira vez)...")
        _processor = AutoProcessor.from_pretrained(MODEL_NAME, token=token)
        _model = Qwen2VLForConditionalGeneration.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,
            device_map="cpu",
            token=token,
        )
        _model.eval()
        print("[IA] Modelo carregado.")
    return _model, _processor


def pdf_para_imagens(pdf_path: Path, temp_dir: Path, dpi: int = 200) -> list[Path]:
    doc = pymupdf.open(pdf_path)
    caminhos = []
    zoom = dpi / 72
    matriz = pymupdf.Matrix(zoom, zoom)
    for i, pagina in enumerate(doc):
        pix = pagina.get_pixmap(matrix=matriz)
        caminho_img = temp_dir / f"{pdf_path.stem}_pagina_{i+1:03d}.png"
        pix.save(str(caminho_img))
        caminhos.append(caminho_img)
    doc.close()
    return caminhos


def extrair_json(imagens: list[Path]) -> dict:
    model, processor = carregar_modelo()

    conteudo = [{"type": "image", "image": str(img)} for img in imagens]
    conteudo.append({"type": "text", "text": INSTRUCAO})
    mensagens = [{"role": "user", "content": conteudo}]

    texto_prompt = processor.apply_chat_template(mensagens, tokenize=False, add_generation_prompt=True)
    imagens_proc, videos_proc = process_vision_info(mensagens)
    entradas = processor(
        text=[texto_prompt],
        images=imagens_proc,
        videos=videos_proc,
        padding=True,
        return_tensors="pt",
    )

    with torch.no_grad():
        saida_ids = model.generate(**entradas, max_new_tokens=1500)

    saida_ids_gerados = [
        ids[len(entrada_ids):] for entrada_ids, ids in zip(entradas.input_ids, saida_ids)
    ]
    resposta = processor.batch_decode(
        saida_ids_gerados, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    resposta = resposta.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(resposta)


def processar_pdf(pdf_path: Path) -> Path:
    temp_dir = pdf_path.parent / ".processado"
    temp_dir.mkdir(exist_ok=True)

    print(f"[IA] Renderizando páginas de '{pdf_path.name}'...")
    imagens = pdf_para_imagens(pdf_path, temp_dir)
    print(f"[IA] {len(imagens)} página(s). Gerando JSON (pode levar minutos em CPU)...")

    try:
        dados = extrair_json(imagens)
    finally:
        for img in imagens:
            img.unlink()

    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    saida = SEEDS_DIR / f"{pdf_path.stem}.json"
    saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return saida


def carregar_manifest(manifest_path: Path) -> dict:
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {}


def salvar_manifest(manifest_path: Path, manifest: dict) -> None:
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--forcar"]
    forcar = "--forcar" in sys.argv
    pasta = Path(args[0]) if args else PASTA_PADRAO

    if not pasta.exists():
        print(f"Pasta '{pasta}' não encontrada.")
        sys.exit(1)

    pdfs = sorted(pasta.glob("*.pdf"))
    if not pdfs:
        print(f"Nenhum PDF encontrado em '{pasta}'.")
        return

    manifest_path = pasta / ".manifest.json"
    manifest = carregar_manifest(manifest_path)

    print(f"[IA] {len(pdfs)} PDF(s) encontrado(s) em '{pasta}'.")

    for pdf in pdfs:
        if not forcar and manifest.get(pdf.name) == "concluido":
            print(f"[SKIP] '{pdf.name}' já processado. Use --forcar pra refazer.")
            continue

        print(f"\n=== Processando {pdf.name} ===")
        try:
            saida = processar_pdf(pdf)
            print(f"[OK] JSON gerado -> {saida}")
            manifest[pdf.name] = "concluido"
        except Exception as e:
            print(f"[ERRO] Falha ao processar '{pdf.name}': {e}")
            manifest[pdf.name] = "erro"
        finally:
            salvar_manifest(manifest_path, manifest)

    print("\nRevise os JSONs em seeds/monstros/ antes de rodar o seed no banco.")


if __name__ == "__main__":
    main()