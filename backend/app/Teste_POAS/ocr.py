"""
Etapa 1 do pipeline (ÚNICA etapa de IA): pega o PDF e, com UM SÓ modelo
rodando local, faz OCR e já devolve o conteúdo estruturado em JSON.

Modelo: Qwen/Qwen2-VL-2B-Instruct
    - É um modelo multimodal (lê imagem + segue instrução), diferente de
      um modelo "só de OCR": ele já entende a pergunta "extraia os campos
      X, Y, Z e responda em JSON" olhando direto pra imagem da página.
    - 2B parâmetros = a opção mais leve dessa família. Roda em CPU (lento),
      mas sem exigir GPU.
    - AVISO: em CPU, gerar a resposta pode levar minutos por monstro.
      Se tiver GPU (mesmo modesta), o ganho de velocidade é grande — nesse
      caso troque MODEL_NAME para "Qwen/Qwen2-VL-7B-Instruct" (mais precisa).
    - AVISO 2: por ser um modelo generalista (não especializado em OCR),
      a precisão de acentuação em português pode variar. Sempre revise o
      JSON gerado antes de rodar a etapa de seed no banco.

Como funciona:
    1. Todas as páginas do PDF viram imagens (via PyMuPDF).
    2. As imagens (podem ser várias, se o monstro ocupar mais de uma
       página) são enviadas numa ÚNICA conversa com o modelo, junto com
       a instrução de schema.
    3. O modelo responde diretamente em JSON — sem etapa de texto bruto
       intermediária.

Primeira execução baixa o modelo (~4-5GB) e guarda em cache local
(~/.cache/huggingface) — só baixa uma vez.

Uso:
    python 1_ocr_extract.py docs/urso-corvo.pdf
    -> gera seeds/monstros/urso-corvo.json
"""

import json
import sys
from pathlib import Path

import fitz  # PyMuPDF
import torch
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from qwen_vl_utils import process_vision_info

MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"
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
  "categoria": string,
  "historia": string
  "dieta": string | null,
  "alvos": string | null,
  "habitats": [string],
}
"""

_model = None
_processor = None


def carregar_modelo():
    global _model, _processor
    if _model is None:
        print(f"[IA] Carregando modelo '{MODEL_NAME}' (pode demorar na primeira vez)...")
        _processor = AutoProcessor.from_pretrained(MODEL_NAME)
        _model = Qwen2VLForConditionalGeneration.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,  # float32 é mais lento mas mais compatível com CPU
            device_map="cpu",
        )
        _model.eval()
    return _model, _processor


def pdf_para_imagens(pdf_path: Path, saida_dir: Path, dpi: int = 200) -> list[Path]:
    doc = fitz.open(pdf_path)
    caminhos = []
    zoom = dpi / 72
    matriz = fitz.Matrix(zoom, zoom)
    for i, pagina in enumerate(doc):
        pix = pagina.get_pixmap(matrix=matriz)
        caminho_img = saida_dir / f"{pdf_path.stem}_pagina_{i+1:03d}.png"
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

    print("[IA] Gerando resposta (pode levar alguns minutos em CPU)...")
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


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python 1_ocr_extract.py <caminho_do_pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    temp_dir = pdf_path.parent / ".processado"
    temp_dir.mkdir(exist_ok=True)

    print(f"[IA] Renderizando páginas de '{pdf_path.name}'...")
    imagens = pdf_para_imagens(pdf_path, temp_dir)
    print(f"[IA] {len(imagens)} página(s) encontradas.")

    try:
        dados = extrair_json(imagens)
    finally:
        for img in imagens:
            img.unlink()

    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    saida = SEEDS_DIR / f"{pdf_path.stem}.json"
    saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[IA] JSON gerado -> {saida}")
    print("Revise o arquivo antes de rodar o seed — confira nomes de traços e acentuação.")


if __name__ == "__main__":
    main()