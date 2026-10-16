"""
Pipeline de Traços:
1. (Opcional) Lê PDFs de './docs' via MarkItDown e extrai os Traços via Groq,
   salvando um JSON de backup em './seeds'. Só roda para PDFs que ainda não
   têm JSON (use forcar_extracao=True para refazer).
2. Insere/atualiza no banco TODOS os JSONs de './seeds' (async).

As tabelas devem existir antes (alembic upgrade head). Groq/MarkItDown só são
importados e a GROQ_API_KEY só é exigida se houver PDF para extrair.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.models.catalogos import Traco
from app.schemas import TracoBase

try:  # opcional: carrega o .env se python-dotenv estiver instalado
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class ListaTracos(BaseModel):
    tracos: List[TracoBase]


DIR_DOCS_TRACOS = Path("app/seeds/extract_tracos/docs")
DIR_SEEDS_TRACOS = Path("app/seeds/extract_tracos/seeds")

MODELO_UNICO = "openai/gpt-oss-120b"

PROMPT_MARKITDOWN = """
Você é um transcritor especialista em manuais de RPG.
Sua tarefa é converter todo o conteúdo visual do documento em Markdown, mantendo os nomes dos traços e suas descrições claramente separados.
"""

_client = None
_md = None


def _get_extratores():
    """Cria os clientes Groq/MarkItDown só quando realmente forem necessários."""
    global _client, _md
    if _client is None:
        chave = os.environ.get("GROQ_API_KEY")
        if not chave or chave == "API":
            raise RuntimeError(
                "GROQ_API_KEY não definida. Configure a variável de ambiente "
                "(ou o .env) para extrair traços de PDFs."
            )
        from groq import Groq
        from markitdown import MarkItDown

        _client = Groq(api_key=chave)
        _md = MarkItDown(
            enable_plugins=True,
            llm_client=_client,
            llm_model=MODELO_UNICO,
            llm_prompt=PROMPT_MARKITDOWN,
        )
    return _client, _md


# ==========================================
# Extração (síncrona, roda em thread)
# ==========================================
def extrair_tracos_com_groq(markdown_text: str) -> str:
    client, _ = _get_extratores()
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
                "content": f"Extraia a lista de traços do seguinte texto:\n\n{markdown_text}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_completion_tokens=8000,
    )

    raw_json_str = (response.choices[0].message.content or "").strip()
    if not raw_json_str:
        raise ValueError("A resposta do modelo veio vazia (possível truncamento).")

    if raw_json_str.startswith("```"):
        raw_json_str = raw_json_str.split("```")[1]
        if raw_json_str.startswith("json"):
            raw_json_str = raw_json_str[4:]
        raw_json_str = raw_json_str.strip()

    parsed_obj = ListaTracos.model_validate_json(raw_json_str)
    return parsed_obj.model_dump_json(indent=2)


def _extrair_pdf_para_json(pdf_path: Path) -> str:
    _, md = _get_extratores()
    result = md.convert(str(pdf_path))
    return extrair_tracos_com_groq(result.text_content)


# ==========================================
# Inserção no banco (async)
# ==========================================
async def inserir_tracos_no_banco(db: AsyncSession, lista: ListaTracos) -> None:
    inseridos = 0
    atualizados = 0

    resultado = await db.execute(select(Traco))
    existentes = {t.nome.strip().upper(): t for t in resultado.scalars().all()}

    for item in lista.tracos:
        nome_traco = item.nome.strip().upper()
        descricao = item.descricao.strip()
        if not nome_traco:
            continue

        traco = existentes.get(nome_traco)
        if traco is None:
            traco = Traco(nome=nome_traco, descricao=descricao)
            db.add(traco)
            existentes[nome_traco] = traco
            inseridos += 1
        else:
            traco.descricao = descricao
            atualizados += 1

    await db.commit()
    print(f"  └─ 💾 Inseridos: {inseridos} | Atualizados: {atualizados}")


# ==========================================
# Fluxo principal
# ==========================================
async def criar_tracos_padrao(forcar_extracao: bool = False) -> int:
    """Retorna o número de erros ocorridos (0 = tudo certo)."""
    DIR_DOCS_TRACOS.mkdir(parents=True, exist_ok=True)
    DIR_SEEDS_TRACOS.mkdir(parents=True, exist_ok=True)
    erros = 0

    # Etapa 1: PDFs -> JSON (só os que ainda não foram extraídos)
    for pdf_path in sorted(DIR_DOCS_TRACOS.glob("*.pdf")):
        destino = DIR_SEEDS_TRACOS / f"{pdf_path.stem}.json"
        if destino.exists() and not forcar_extracao:
            continue

        print(f"📄 Extraindo traços de: {pdf_path.name}...")
        try:
            json_str = await asyncio.to_thread(_extrair_pdf_para_json, pdf_path)
            destino.write_text(json_str, encoding="utf-8")
            print(f"  ├─ 📝 JSON salvo em '{destino}'")
        except Exception as e:
            erros += 1
            print(f"  └─ ❌ Erro ao extrair {pdf_path.name}: {e}\n")

    # Etapa 2: JSON -> banco
    arquivos_json = sorted(DIR_SEEDS_TRACOS.glob("*.json"))
    if not arquivos_json:
        print(f"Nenhum JSON de traços encontrado em '{DIR_SEEDS_TRACOS}'.")
        return erros

    for json_path in arquivos_json:
        print(f"🌱 Inserindo traços de: {json_path.name}...")
        try:
            lista = ListaTracos.model_validate_json(json_path.read_text(encoding="utf-8"))
            async with AsyncSessionLocal() as db:
                await inserir_tracos_no_banco(db, lista)
        except Exception as e:
            erros += 1
            print(f"  └─ ❌ Erro ao inserir {json_path.name}: {e}\n")

    return erros


async def _main() -> None:
    try:
        await criar_tracos_padrao()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())