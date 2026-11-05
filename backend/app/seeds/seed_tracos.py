import asyncio
import re
import pymupdf
from sqlalchemy import select

# Ajuste os imports abaixo caso os ficheiros estejam noutras diretorias
from app.database import AsyncSessionLocal
from app.models.catalogos import Traco
from app.schemas.catalogos_enums import TracoCreate

def extrair_tracos_do_pdf(caminho_pdf: str) -> list[TracoCreate]:
    """Lê o PDF com PyMuPDF e extrai os traços utilizando expressões regulares."""
    padrao = re.compile(r'^[•\s]*([A-ZÇÃÕÁÉÍÓÚÂÊÔ\s0-9]+?)\s*(?:->|→)?\s*(\(.*)')
    tracos_extraidos = []
    
    # Abre o documento ignorando erros estruturais de fontes
    with pymupdf.open(caminho_pdf) as pdf:
        nome_atual = None
        descricao_atual = ""

        for pagina in pdf:
            texto = pagina.get_text()
            if not texto:
                continue
                
            for linha in texto.split('\n'):
                linha = linha.strip()
                
                # Ignora cabeçalhos, rodapés vazios ou números isolados
                if not linha or linha == "TRAÇOS" or linha.isdigit():
                    continue
                    
                match = padrao.match(linha)
                
                if match:
                    if nome_atual:
                        tracos_extraidos.append(TracoCreate(nome=nome_atual.strip(), descricao=descricao_atual.strip()))
                    
                    nome_atual = match.group(1).strip()
                    descricao_atual = match.group(2).strip()
                elif nome_atual:
                    descricao_atual += " " + linha

        if nome_atual:
            tracos_extraidos.append(TracoCreate(nome=nome_atual.strip(), descricao=descricao_atual.strip()))
            
    return tracos_extraidos


async def criar_tracos_padrao(tracos: list[TracoCreate]):
    async with AsyncSessionLocal() as db:
        resultado = await db.execute(select(Traco))
        existentes = {t.nome.strip().upper(): t for t in resultado.scalars().all()}
        
        inseridos = 0
        atualizados = 0

        for item in tracos:
            nome_upper = item.nome.strip().upper()
            
            traco_db = existentes.get(nome_upper)
            if traco_db is None:
                novo_traco = Traco(nome=item.nome, descricao=item.descricao)
                db.add(novo_traco)
                existentes[nome_upper] = novo_traco
                inseridos += 1
            else:
                traco_db.descricao = item.descricao
                atualizados += 1

        await db.commit()
        print(f"Base de dados atualizada: {inseridos} inseridos, {atualizados} atualizados.")


async def pipeline_criar_tracos():
    print("A extrair dados do PDF...")
    lista_tracos = extrair_tracos_do_pdf("app/seeds/extract_tracos/docs/Traços.pdf")
    
    if not lista_tracos:
        print("Nenhum traço encontrado no documento.")
        return

    print(f"Foram encontrados {len(lista_tracos)} traços. A guardar na base de dados...")
    await criar_tracos_padrao(lista_tracos)


if __name__ == "__main__":
    asyncio.run(pipeline_criar_tracos())