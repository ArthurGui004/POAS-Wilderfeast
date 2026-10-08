import os
import json
import shutil
import warnings
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from markitdown import MarkItDown
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
# 2. Configurações de Diretórios e APIs
# ==========================================
os.environ["GROQ_API_KEY"] = "API"

DIR_DOCS = Path("./app/Teste_POAS/docs")
DIR_PROCESSADO = DIR_DOCS / ".processado"
DIR_SEEDS = Path("./app/Teste_POAS/seeds")
MANIFEST_FILE = DIR_DOCS / ".manifest.json"

DIR_PROCESSADO.mkdir(parents=True, exist_ok=True)
DIR_SEEDS.mkdir(parents=True, exist_ok=True)

MODELO_UNICO = "openai/gpt-oss-120b"
PROMPT_MARKITDOWN = """
Você é um transcritor especialista em layout de fichas de RPG.
Sua tarefa é converter todo o conteúdo visual e estrutural do documento em Markdown impecável.

Siga estas regras estritas de transcrição:
1. PRESERVAÇÃO DE ATRIBUTOS E NÚMEROS:
   - Identifique caixas de atributos (como ESTILOS e HABILIDADES) e mantenha os pares Chave: Valor exatamente como aparecem visualmente (ex: "PODEROSO: 4", "LIGEIRO: 0", "ARMAZENAR: +1").
   - Interprete círculos vazios, letras 'O' ou ícones de preenchimento em blocos de atributos numéricos como o número 0, caso representem valor nulo.

2. ESTRUTURA DE PARTES E EQUIPAMENTOS:
   - Para cada item na seção PARTES, preserve o Nome da Parte (ex: CASCO, PÉS), Durabilidade, Alcance e seus blocos internos "Passiva:" e "Se Quebrado:".
   - Mantenha valores de Alcance completos se contiverem texto explicativo (ex: "Alcance: 1 (GOLPEAR PODEROSO)").

3. COLUNAS E HIERARQUIA:
   - Não misture colunas paralelas. Mantenha os cabeçalhos das seções (ESTILOS, HABILIDADES, TRAÇOS, PARTES, COMPORTAMENTO, DIETA, HÁBITAT) bem delimitados com Markdown (#, ##, ###).
   - Transcreva todo o texto descritivo e passivas sem resumir ou omitir parágrafos.
"""

client = Groq()


md = MarkItDown(
    enable_plugins=True,
    llm_client=client,
    llm_model= MODELO_UNICO,
    llm_prompt="Descreva esta ficha de RPG preservando a ordem visual das colunas e caixas de texto separadamente."
)

# ==========================================
# 3. Funções Auxiliares do Manifest
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

# ==========================================
# 4. Chamada à Groq para Estruturação JSON
# ==========================================
def extrair_json_com_groq(markdown_text: str) -> str:
    schema_json = FichaMonstro.model_json_schema()

    system_prompt = (
        "Você é um extrator de dados especialista em fichas de RPG de layout coluna.\n"
        "ATENÇÃO: O texto de entrada foi extraído de um PDF de 2 colunas e pode estar entrelançado horizontalmente!\n\n"
        "REGRAS DE DESENTRELAÇAMENTO E RECONSTRUÇÃO:\n"
        "1. ESTILOS E HABILIDADES:\n"
        "   - Separe os Estilos (LIGEIRO: 0, PODEROSO: 4, PRECISO: 0, SAGAZ: 0).\n"
        "   - Separe as Habilidades com seus valores (ex: ARMAZENAR: 1, ASSEGURAR: 3, CURAR: 3, PROCURAR: 1).\n\n"
        "2. TRAÇOS vs TRAÇOS ADICIONAIS:\n"
        "   - Traços principais contêm o nome e a descrição com '(Passiva)' ou '(Custo: ...)'. Ex: ARMADURA NATURAL, ELECTRORRECEPTIVIDADE, GIGANTESCO, RECUO, ROBUSTO.\n"
        "   - Expressões em caixa alta sem descrição extensa como 'DEVORADOR DE ENERGIA', 'MIGRADOR', 'POLINIZADOR' são 'tracos_adicionais'. NÃO as misture no texto das descrições.\n\n"
        "3. PARTES:\n"
        "   - Extraia as partes (ex: CASCO, PÉS).\n"
        "   - Associe a durabilidade (ex: 30) e alcance para cada parte correspondente.\n\n"
        "4. FORMATO DE SAÍDA:\n"
        "   - Retorne APENAS UM único objeto JSON válido. Responda estritamente em formato JSON.\n\n"
        f"{json.dumps(schema_json, ensure_ascii=False)}"
    )

    response = client.chat.completions.create(
        model=MODELO_UNICO,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": f"Extraia os dados da seguinte ficha e retorne a resposta estritamente em formato json:\n\n{markdown_text}"
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_completion_tokens=30000
    )
    
    raw_json_str = response.choices[0].message.content.strip()

    # 1. Remove marcadores markdown
    if raw_json_str.startswith("```"):
        raw_json_str = raw_json_str.split("```")[1]
        if raw_json_str.startswith("json"):
            raw_json_str = raw_json_str[4:]
        raw_json_str = raw_json_str.strip()

    # 2. Trata duplicação de JSON
    if "}{" in raw_json_str:
        raw_json_str = raw_json_str.split("}{")[0] + "}"

    # 3. Valida e formata via Pydantic
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
        
        print(f"📄 Processando com MarkItDown + Groq ({MODELO_UNICO}): {nome_arquivo}...")
        
        try:
            # 1. OCR e preservação de estrutura via MarkItDown
            result = md.convert(str(pdf_path))
            markdown_content = result.text_content

            # 2. Conversão para JSON estruturado via Groq
            json_resultado = extrair_json_com_groq(markdown_content)

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