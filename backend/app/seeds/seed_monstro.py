"""
Etapa 3 do pipeline: insere/atualiza monstros no banco de dados percorrendo 
todos os arquivos JSON da pasta './seeds'.
"""

import json
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.enums import CategoriaMonstro
from app.models import (
    Monstro,
    MonstroEstilo,
    MonstroHabilidade,
    MonstroParte,
    Estilo,
    Habilidade,
    Traco,
    Tecnica
)

DIR_SEEDS_PADRAO = Path("./seeds")


def seed_monstro(session: Session, dados: dict) -> None:
    # 1. Busca ou cria a instância base do Monstro
    nome_monstro = dados.get("nome")
    if not nome_monstro:
        raise ValueError("O JSON fornecido não contém o campo 'nome'.")

    monstro = session.query(Monstro).filter_by(nome=nome_monstro).first()
    if monstro is None:
        monstro = Monstro(nome=nome_monstro)
        session.add(monstro)

    # 2. Atributos Básicos
    cat_str = dados.get("categoria", "")
    try:
        monstro.categoria = CategoriaMonstro[cat_str.upper()] if cat_str else list(CategoriaMonstro)[0]
    except (KeyError, IndexError):
        monstro.categoria = list(CategoriaMonstro)[0]

    monstro.vigor_base = int(dados.get("vigor_base") or dados.get("durabilidade") or 30)
    monstro.vigor_atual = int(dados.get("vigor_atual") or monstro.vigor_base)

    monstro.historia = dados.get("historia") or dados.get("comportamento")
    monstro.alvos = dados.get("alvos")

    # Dieta e Habitat (converte listas para strings formatadas)
    dieta_raw = dados.get("dieta")
    if isinstance(dieta_raw, list):
        monstro.dieta = ", ".join(filter(None, dieta_raw))
    else:
        monstro.dieta = dieta_raw

    habitat_raw = dados.get("habitat")
    if isinstance(habitat_raw, list):
        monstro.habitat = ", ".join(filter(None, habitat_raw))
    else:
        monstro.habitat = habitat_raw

    # 3. Estilos (MonstroEstilo)
    monstro.estilos.clear()
    estilos_dados = dados.get("estilos", {})
    if isinstance(estilos_dados, dict):
        for nome_estilo, pontos in estilos_dados.items():
            if pontos is None:
                continue
            
            estilo_obj = session.query(Estilo).filter(Estilo.nome.ilike(nome_estilo)).first()
            if estilo_obj:
                monstro.estilos.append(MonstroEstilo(estilo=estilo_obj, pontos=int(pontos)))
            else:
                print(f"  [AVISO] Estilo '{nome_estilo}' não encontrado no banco — pulando.")

    # 4. Habilidades (MonstroHabilidade)
    monstro.habilidades.clear()
    for hab_item in dados.get("habilidades", []):
        if isinstance(hab_item, dict):
            nome_hab = hab_item.get("nome")
            pontos_hab = hab_item.get("valor", 0)
        else:
            nome_hab = str(hab_item)
            pontos_hab = 0

        if not nome_hab:
            continue

        hab_obj = session.query(Habilidade).filter(Habilidade.nome.ilike(nome_hab)).first()
        if hab_obj:
            monstro.habilidades.append(MonstroHabilidade(habilidade=hab_obj, pontos=int(pontos_hab)))
        else:
            print(f"  [AVISO] Habilidade '{nome_hab}' não encontrada no banco — pulando.")

    # 5. Traços (Tabela de Associação Secundária N:N)
    novos_tracos = []
    nomes_tracos = []

    for t in dados.get("tracos", []):
        if isinstance(t, dict) and t.get("nome"):
            nomes_tracos.append(t.get("nome"))
        elif isinstance(t, str):
            nomes_tracos.append(t)

    for t_adj in dados.get("tracos_adicionais", []):
        if isinstance(t_adj, str):
            nomes_tracos.append(t_adj)

    for nome_t in nomes_tracos:
        traco_obj = session.query(Traco).filter(Traco.nome.ilike(nome_t)).first()
        if traco_obj:
            if traco_obj not in novos_tracos:
                novos_tracos.append(traco_obj)
        else:
            print(f"  [AVISO] Traço '{nome_t}' não encontrado no banco — pulando.")

    monstro.tracos = novos_tracos

    # 6. Partes do Monstro (MonstroParte)
    monstro.partes.clear()
    for parte_data in dados.get("partes", []):
        if not isinstance(parte_data, dict):
            continue

        nome_parte = parte_data.get("nome")
        if not nome_parte:
            continue

        dur_max = parte_data.get("durabilidade") or 30
        dur_atual = parte_data.get("durabilidade_atual", dur_max)
        alcance = parte_data.get("alcance")
        se_quebrado_val = bool(parte_data.get("se_quebrado"))

        nome_tecnica = parte_data.get("tecnica") or nome_parte
        tecnica_obj = session.query(Tecnica).filter(Tecnica.nome.ilike(nome_tecnica)).first()
        if not tecnica_obj:
            tecnica_obj = session.query(Tecnica).first()

        if not tecnica_obj:
            print(f"  [AVISO] Nenhuma Técnica cadastrada no banco para associar à parte '{nome_parte}' — pulando parte.")
            continue

        monstro_parte = MonstroParte(
            nome=nome_parte,
            tecnica=tecnica_obj,
            alcance=str(alcance) if alcance is not None else None,
            durabilidade_max=int(dur_max),
            durabilidade_atual=int(dur_atual),
            se_quebrado=se_quebrado_val
        )
        monstro.partes.append(monstro_parte)

    # Persiste as alterações no banco
    session.commit()
    print(f"  ✅ Salvo no banco: Monstro '{monstro.nome}' (id={monstro.id}).")


def main() -> None:
    # Define o diretório a ser percorrido (padrão: ./seeds)
    if len(sys.argv) > 1:
        dir_seeds = Path(sys.argv[1])
    else:
        dir_seeds = DIR_SEEDS_PADRAO

    if not dir_seeds.exists():
        print(f"❌ O diretório '{dir_seeds}' não existe.")
        sys.exit(1)

    # Busca todos os arquivos .json na pasta
    if dir_seeds.is_file() and dir_seeds.suffix == ".json":
        arquivos_json = [dir_seeds]
    else:
        arquivos_json = sorted(list(dir_seeds.glob("*.json")))

    if not arquivos_json:
        print(f"Nenhum arquivo .json encontrado na pasta '{dir_seeds}'.")
        return

    print(f"🌱 Encontrados {len(arquivos_json)} arquivo(s) JSON para popular o banco de dados...\n")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    sucesso_count = 0
    erro_count = 0

    try:
        for arquivo_path in arquivos_json:
            print(f"📄 Processando seed: {arquivo_path.name}...")
            try:
                dados = json.loads(arquivo_path.read_text(encoding="utf-8"))
                seed_monstro(db, dados)
                sucesso_count += 1
            except Exception as e:
                db.rollback()
                erro_count += 1
                print(f"  ❌ Erro ao processar '{arquivo_path.name}': {e}")
            print("-" * 50)
    finally:
        db.close()

    print(f"\n✨ Processamento finalizado! Sucessos: {sucesso_count} | Erros: {erro_count}")


if __name__ == "__main__":
    main()