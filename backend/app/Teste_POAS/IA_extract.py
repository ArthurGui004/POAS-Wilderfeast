import json
import sys
from pathlib import Path
import ollama

SEEDS_DIR = Path("seeds/monstros")
OLLAMA_MODEL = "qwen3.5:2b"

SYSTEM_PROMPT = """\
Você é um extrator de dados de RPG (sistema Wilderfeast). 
Analise o texto e retorne APENAS um objeto JSON no formato exigido.
Não invente dados. Se um campo não existir no texto, use null para strings e [] para listas.

Schema exato:
{
  "nome": "string",
  "dieta": "string ou null",
  "comportamento": "string ou null",
  "descricao": "string ou null",
  "habitats": ["string"],
  "tracos": ["string em MAIÚSCULAS"],
  "habilidades": ["string"]
}
"""


def extrair_json_local(texto: str) -> dict:
    # A própria biblioteca já cuida da conexão e da porta do Ollama
    resposta = ollama.generate(
        model=OLLAMA_MODEL,
        prompt=f"{SYSTEM_PROMPT}\n\nTexto do monstro:\n{texto}",
        format="json",
    )
    return json.loads(resposta["response"])


def extrair_json_de_md(md_path: Path) -> Path:
    texto = md_path.read_text(encoding="utf-8")
    dados = extrair_json_local(texto)

    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    saida = SEEDS_DIR / f"{md_path.stem}.json"
    saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[EXTRACT] JSON gerado via Ollama ({OLLAMA_MODEL}) -> {saida}")
    return saida