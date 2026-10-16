"""
Pipeline Dinâmico para Traços:
1. Lê PDFs de regras/traços da pasta './docs/tracos' via MarkItDown.
2. Extrai um JSON estruturado com todos os Traços (nome e descrição) via Groq.
3. Salva o JSON na pasta './seeds/tracos' (backup/auditoria).
4. Insere/Atualiza os dados diretamente no Banco via SQLAlchemy.
"""

import json
import os
from pathlib import Path
from typing import List

from groq import Groq
from markitdown import MarkItDown
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import AsyncSessionLocal, Base, engine
from app.models.catalogos import Traco
from app.schemas import TracoBase

class ListaTracos(BaseModel):
    tracos: List[TracoBase]

# ==========================================
# 2. Configurações
# ==========================================
os.environ["GROQ_API_KEY"] = "API"

DIR_DOCS_TRACOS = Path("app/seeds/extract_tracos/docs")
DIR_SEEDS_TRACOS = Path("app/seeds/extract_tracos/seeds")

DIR_DOCS_TRACOS.mkdir(parents=True, exist_ok=True)
DIR_SEEDS_TRACOS.mkdir(parents=True, exist_ok=True)

MODELO_UNICO = "openai/gpt-oss-120b"
client = Groq()

PROMPT_MARKITDOWN = """
Você é um transcritor especialista em manuais de RPG.
Sua tarefa é converter todo o conteúdo visual do documento em Markdown, mantendo os nomes dos traços e suas descrições claramente separados.
"""

md = MarkItDown(
    enable_plugins=True,
    llm_client=client,
    llm_model=MODELO_UNICO,
    llm_prompt=PROMPT_MARKITDOWN
)

# ==========================================
# 3. Funções de Extração e Seed
# ==========================================
def extrair_tracos_com_groq(markdown_text: str) -> str:
    schema_json = ListaTracos.model_json_schema()

    system_prompt = (
        "Você é um assistente especialista em extrair dados de regras de RPG.\n"
        "Sua tarefa é ler o texto fornecido e extrair TODOS os traços, habilidades ou passivas listadas.\n"
        "Retorne ESTRITAMENTE um objeto JSON válido que siga este esquema JSON Schema:\n\n"
        f"{json.dumps(schema_json, ensure_ascii=False)}\n\n"
        "REGRAS DE EXTRAÇÃO:\n"
        "1. Responda APENAS com o objeto JSON puro. NÃO use blocos de código (```json ... ```).\n"
        "2. O campo 'nome' deve estar em MAIÚSCULAS.\n"
        "3. O campo 'descricao' deve conter o texto exato da regra, incluindo custos de ação (ex: '(1 Ação)', '(Passiva)').\n"
    )

    response = client.chat.completions.create(
        model=MODELO_UNICO,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": f"Extraia a lista de traços do seguinte texto:\n\n{markdown_text}"
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_completion_tokens=4000
    )
    
    raw_json_str = response.choices[0].message.content.strip()
    
    if raw_json_str.startswith("```"):
        raw_json_str = raw_json_str.split("```")[1]
        if raw_json_str.startswith("json"):
            raw_json_str = raw_json_str[4:]
        raw_json_str = raw_json_str.strip()

    parsed_obj = ListaTracos.model_validate_json(raw_json_str)
    return parsed_obj.model_dump_json(indent=2)

def inserir_tracos_no_banco(session: Session, dados_json: dict) -> None:
    lista_tracos = dados_json.get("tracos", [])
    inseridos = 0
    atualizados = 0

    for item in lista_tracos:
        nome_traco = item["nome"].strip().upper()
        descricao = item["descricao"].strip()

        traco = session.query(Traco).filter_by(nome=nome_traco).first()
        if traco is None:
            traco = Traco(nome=nome_traco, descricao=descricao)
            session.add(traco)
            inseridos += 1
        else:
            traco.descricao = descricao
            atualizados += 1

    session.commit()
    print(f"  └─ 💾 Inseridos: {inseridos} | Atualizados: {atualizados}")

# ==========================================
# 4. Execução do Fluxo
# ==========================================
def processar_pdfs_tracos():
    arquivos_pdf = [f for f in DIR_DOCS_TRACOS.glob("*.pdf") if f.is_file()]

    if not arquivos_pdf:
        print(f"Nenhum PDF encontrado na pasta '{DIR_DOCS_TRACOS}'.")
        return

    Base.metadata.create_all(bind=engine)
    db = AsyncSessionLocal()

    print(f"🚀 Iniciando extração de Traços em {len(arquivos_pdf)} arquivo(s)...\n")

    try:
        for pdf_path in arquivos_pdf:
            print(f"📄 Processando: {pdf_path.name}...")
            
            try:
                # 1. OCR / Leitura via MarkItDown
                result = md.convert(str(pdf_path))
                
                # 2. Extração Estruturada via Groq
                json_str = extrair_tracos_com_groq(result.text_content)
                dados_dict = json.loads(json_str)

                # 3. Salvar Backup JSON
                arquivo_seed = DIR_SEEDS_TRACOS / f"{pdf_path.stem}.json"
                with open(arquivo_seed, "w", encoding="utf-8") as f:
                    f.write(json_str)
                print(f"  ├─ 📝 JSON salvo em '{arquivo_seed}'")

                # 4. Inserção no Banco
                inserir_tracos_no_banco(db, dados_dict)

            except Exception as e:
                db.rollback()
                print(f"  └─ ❌ Erro ao processar {pdf_path.name}: {e}\n")
    finally:
        db.close()
        print("\n✨ Processo finalizado!")

if __name__ == "__main__":
    processar_pdfs_tracos()