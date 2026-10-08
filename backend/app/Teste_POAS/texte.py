import os
import json
import shutil
import warnings
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import pypdfium2 as pdfium
import torch
from transformers import AutoProcessor, GlmOcrForConditionalGeneration
from groq import Groq

# Silencia avisos no terminal
warnings.filterwarnings("ignore")

# ==========================================
# 1. Schemas de Dados (Pydantic Resilientes)
# ==========================================
class Estilos(BaseModel):
    ligeiro: Optional[int] = None
    poderoso: Optional[int] = None
    preciso: Optional[int] = None
    sagaz: Optional[int] = None

class Habilidade(BaseModel):
    nome: str
    valor: int

class Traco(BaseModel):
    nome: str
    descricao: str

class Parte(BaseModel):
    nome: str
    durabilidade: Optional[int] = None
    alcance: Optional[str] = None
    passiva: Optional[str] = None
    se_quebrado: Optional[str] = None

class FichaMonstro(BaseModel):
    nome: str
    estilos: Estilos
    habilidades: List[Habilidade] = []
    tracos: List[Traco] = []
    tracos_adicionais: List[str] = []
    partes: List[Parte] = []
    comportamento: Optional[str] = None
    dieta: Optional[List[str]] = None
    habitat: List[str] = []

# ==========================================
# 2. Configurações de Diretórios, API e IA Local
# ==========================================
os.environ["GROQ_API_KEY"] = "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"

DIR_DOCS = Path("./docs")
DIR_PROCESSADO = DIR_DOCS / ".processado"
DIR_SEEDS = Path("./seeds")
MANIFEST_FILE = DIR_DOCS / ".manifest.json"

DIR_PROCESSADO.mkdir(parents=True, exist_ok=True)
DIR_SEEDS.mkdir(parents=True, exist_ok=True)

MODELO_GROQ = "openai/gpt-oss-120b"
MODELO_LOCAL_ID = "zai-org/GLM-OCR"

# Carregamento do modelo GLM-OCR Local
print("⏳ Carregando modelo local GLM-OCR...")
processor = AutoProcessor.from_pretrained(MODELO_LOCAL_ID)
model_ocr = GlmOcrForConditionalGeneration.from_pretrained(
    MODELO_LOCAL_ID,
    device_map="auto",
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32
)

client_groq = Groq()

# ==========================================
# 3. Funções Auxiliares
# ==========================================
def carregar_manifest() -> dict:
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def salvar_manifest(manifest: dict):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

def extrair_texto_pdf_com_glm_ocr(pdf_path: Path) -> str:
    """Renderiza cada página do PDF em imagem e realiza OCR via GLM-OCR local."""
    pdf = pdfium.PdfDocument(pdf_path)
    texto_paginas = []

    for page_idx, page in enumerate(pdf):
        # Renderiza a página em imagem com escala 2x para melhor precisão
        image = page.render(scale=2).to_pil()

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": "Text Recognition:"}
                ]
            }
        ]

        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        ).to(model_ocr.device)

        input_len = inputs["input_ids"].shape[1]
        
        with torch.no_grad():
            output = model_ocr.generate(**inputs, max_new_tokens=2048)
        
        texto_extraido = processor.decode(output[0][input_len:], skip_special_tokens=True)
        texto_paginas.append(texto_extraido)

    return "\n\n--- NOVA PÁGINA ---\n\n".join(texto_paginas)

# ==========================================
# 4. Estruturação JSON via Groq
# ==========================================
def extrair_json_com_groq(markdown_text: str) -> str:
    schema_json = FichaMonstro.model_json_schema()

    system_prompt = (
        "Você é um extrator de dados especialista em fichas de RPG.\n"
        "Sua tarefa é analisar o texto recebido e retornar ESTRITAMENTE "
        "um objeto JSON válido que siga este esquema JSON Schema:\n\n"
        f"{json.dumps(schema_json, ensure_ascii=False)}\n\n"
        "REGRAS CRÍTICAS DE FORMATO:\n"
        "1. Responda APENAS com o objeto JSON puro. NÃO use blocos de código com três crases (```json ... ```).\n"
        "2. Sua resposta DEVE começar diretamente com o caractere '{' e terminar com '}'.\n"
        "3. Inclua TODOS os campos do esquema no JSON. Se um campo não existir no texto, defina como null ou [] (lista vazia).\n"
        "4. Em TRAÇOS e PARTES, capture o texto completo sem resumir.\n"
        "5. 'Traços' e 'Traços Adicionais' são listas separadas — não misture.\n"
        "6. Em PARTES, 'se_quebrado' é o texto após 'Se Quebrado(a):', se existir.\n"
        "7. 'alcance' de uma Parte só existe se o card mostrar 'Alcance: N'."
    )

    response = client_groq.chat.completions.create(
        model=MODELO_GROQ,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": f"Extraia os dados da seguinte ficha e retorne a resposta estritamente em formato json:\n\n{markdown_text}"
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_completion_tokens=3000
    )
    
    raw_json_str = response.choices[0].message.content.strip()
    
    if raw_json_str.startswith("```"):
        raw_json_str = raw_json_str.split("```")[1]
        if raw_json_str.startswith("json"):
            raw_json_str = raw_json_str[4:]
        raw_json_str = raw_json_str.strip()

    parsed_obj = FichaMonstro.model_validate_json(raw_json_str)
    return parsed_obj.model_dump_json(indent=2)

# ==========================================
# 5. Execução do Fluxo Completo
# ==========================================
def processar_fluxo():
    manifest = carregar_manifest()
    arquivos_pdf = [f for f in DIR_DOCS.glob("*.pdf") if f.is_file()]
    
    if not arquivos_pdf:
        print("Nenhum arquivo PDF pendente encontrado na pasta 'docs'.")
        return

    for pdf_path in arquivos_pdf:
        nome_arquivo = pdf_path.name
        timestamp_atual = datetime.now().isoformat()
        
        print(f"📄 Processando com GLM-OCR (Local) + Groq ({MODELO_GROQ}): {nome_arquivo}...")
        
        try:
            # 1. OCR Visual via GLM-OCR Local
            texto_ocr = extrair_texto_pdf_com_glm_ocr(pdf_path)

            # 2. Estruturação para JSON via Groq
            json_resultado = extrair_json_com_groq(texto_ocr)

            # 3. Salva o JSON na pasta /seeds
            arquivo_seed = DIR_SEEDS / f"{pdf_path.stem}.json"
            with open(arquivo_seed, "w", encoding="utf-8") as f:
                f.write(json_resultado)

            # 4. Move o PDF para /docs/.processado
            destino_processado = DIR_PROCESSADO / nome_arquivo
            shutil.move(str(pdf_path), str(destino_processado))

            # 5. Registra o sucesso no .manifest.json
            manifest[nome_arquivo] = {
                "status": "sucesso",
                "processado_em": timestamp_atual,
                "output_seed": str(arquivo_seed),
                "localizacao_atual": str(destino_processado)
            }
            print(f"✅ Sucesso: JSON gerado em {arquivo_seed} e PDF movido.")

        except Exception as e:
            manifest[nome_arquivo] = {
                "status": "erro",
                "processado_em": timestamp_atual,
                "erro_mensagem": str(e)
            }
            print(f"❌ Erro ao processar {nome_arquivo}: {e}")
            
        finally:
            salvar_manifest(manifest)

if __name__ == "__main__":
    processar_fluxo()