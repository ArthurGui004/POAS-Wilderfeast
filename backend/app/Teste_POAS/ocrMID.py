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
# 1. Schemas de Dados (Pydantic)
# ==========================================
class Estilos(BaseModel):
    ligeiro: int
    poderoso: int
    preciso: int
    sagaz: int

class Habilidade(BaseModel):
    nome: str
    valor: int

class Traco(BaseModel):
    nome: str
    descricao: str

class Parte(BaseModel):
    nome: str
    durabilidade: Optional[int] = None
    alcance: Optional[int] = None
    passiva: Optional[str] = None
    se_quebrado: Optional[str] = None

class FichaMonstro(BaseModel):
    nome: str
    estilos: Estilos
    habilidades: List[Habilidade]
    tracos: List[Traco]
    tracos_adicionais: List[str]
    partes: List[Parte]
    comportamento: Optional[str] = None
    dieta: Optional[str] = None
    habitat: List[str]

# ==========================================
# 2. Configurações de Diretórios e API
# ==========================================
os.environ["GROQ_API_KEY"] = "API"

DIR_DOCS = Path("./app/Teste_POAS/docs")
DIR_PROCESSADO = DIR_DOCS / ".processado"
DIR_SEEDS = Path("./app/Teste_POAS/seeds")
MANIFEST_FILE = DIR_DOCS / ".manifest.json"

DIR_PROCESSADO.mkdir(parents=True, exist_ok=True)
DIR_SEEDS.mkdir(parents=True, exist_ok=True)

client = Groq()
md = MarkItDown(
    enable_plugins=True,
    llm_client=client,
    llm_model="openai/gpt-oss-120b",
    llm_prompt="Extraia todo o texto da tabela e preserve a estrutura"
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
# 4. Chamada à Groq com Validação de Schema
# ==========================================
def extrair_json_com_groq(markdown_text: str) -> str:
    schema_json = FichaMonstro.model_json_schema()
    
    modelos_candidatos = ["openai/gpt-oss-120b"]
    
    system_prompt = (
                    '''Você é um extrator de dados especialista em fichas de RPG.
                    Sua tarefa é analisar o texto recebido e retornar ESTRITAMENTE
                    um objeto JSON válido que siga perfeitamente este esquema JSON Schema:
                      
                    Regras importantes:
                    - Não invente informação que não está na imagem: campo não encontrado
                    vira null (string), 0 (número) ou lista vazia (lista).
                    - Poderoso, Ligeiro, Capsioso e Sagaz são estilos
                    - Agarrar, Armazenamento, Assegurar, Atirar, Atravessar, Chamar, Curar, Estudar, Exibir, Golpear, Manufaturar, Procurar são Habilidades
                    - Em TRAÇOS e PARTES, capture o texto completo do efeito como está
                    escrito no card, não resuma.
                    - "Traços" e "Traços Adicionais" são listas separadas — não misture.
                    - Em PARTES, "se_quebrado" é o texto que aparece após "Se Quebrado(a):"
                    dentro daquela parte, se existir.
                    - "alcance" de uma Parte só existe se o card mostrar algo como
                    "Alcance: N" perto do nome da Parte.\n'''
                    f"{json.dumps(schema_json, ensure_ascii=False)}"
                )

    ultimo_erro = None
    for modelo in modelos_candidatos:
        try:
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extraia os dados da seguinte ficha:\n\n{markdown_text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            raw_json_str = response.choices[0].message.content
            parsed_obj = FichaMonstro.model_validate_json(raw_json_str)
            return parsed_obj.model_dump_json(indent=2)
            
        except Exception as e:
            if "model_not_found" in str(e) or "404" in str(e):
                ultimo_erro = e
                continue
            raise e

    raise Exception(f"Falha ao chamar a API Groq. Erro: {ultimo_erro}")

# ==========================================
# 5. Execução do Fluxo
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
        
        print(f"📄 Processando com MarkItDown + Groq: {nome_arquivo}...")
        
        try:
            # 1. Extração de texto via MarkItDown
            result = md.convert(str(pdf_path))
            markdown_content = result.text_content
            print(markdown_content)
            
            # 2. Extração Estruturada via Groq
            # json_resultado = extrair_json_com_groq(markdown_content)
            # print(f'RESULTADO JSON\n{json_resultado}')

            # # 3. Salva o JSON na pasta /seeds
            arquivo_seed = DIR_SEEDS / f"{pdf_path.stem}.json"
            # with open(arquivo_seed, "w", encoding="utf-8") as f:
            #     f.write(json_resultado)

            # # 4. Move o PDF para /docs/.processado
            destino_processado = DIR_PROCESSADO / nome_arquivo
            # shutil.move(str(pdf_path), str(destino_processado))

            # 5. Atualiza o .manifest.json
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