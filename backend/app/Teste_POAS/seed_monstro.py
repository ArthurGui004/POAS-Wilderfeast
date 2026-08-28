"""
Etapa 3 do pipeline: insere/atualiza um monstro no banco a partir do
JSON gerado na etapa 2, resolvendo nomes de traço/habilidade/habitat
para os IDs correspondentes (você nunca escreve ID no JSON à mão).

AJUSTE conforme seus models reais — este arquivo assume:
    Monstro(id, nome, dieta, comportamento, descricao)
    Traco(id, nome, ...)
    Habilidade(id, nome, ...)
    Habitat(id, nome)
    monstro_traco       <- tabela de associação N:N
    monstro_habilidade  <- tabela de associação N:N
    monstro_habitat     <- tabela de associação N:N

Se algum nome do JSON não existir no banco (traço com erro de digitação,
por exemplo), o script AVISA e pula aquele item em vez de falhar
silenciosamente ou quebrar o resto da importação.

Uso:
    python 3_seed_monstro.py seeds/monstros/urso-corvo.json
"""

import json
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# --- AJUSTE PARA O SEU PROJETO ---
from database import SessionLocal, engine
from models import Base, Monstro, Traco, Habilidade, Habitat
# -----------------------------------


def resolver_por_nome(session: Session, model, nomes: list[str]):
    """Busca cada nome no banco; avisa e ignora os que não existem."""
    objetos = []
    for nome in nomes:
        obj = session.query(model).filter_by(nome=nome).first()
        if obj is None:
            print(f"  [AVISO] {model.__name__} '{nome}' não encontrado no banco — pulando.")
            continue
        objetos.append(obj)
    return objetos


def seed_monstro(session: Session, dados: dict) -> None:
    monstro = session.query(Monstro).filter_by(nome=dados["nome"]).first()
    if monstro is None:
        monstro = Monstro(nome=dados["nome"])
        session.add(monstro)

    monstro.dieta = dados.get("dieta")
    monstro.comportamento = dados.get("comportamento")
    monstro.descricao = dados.get("descricao")

    monstro.tracos = resolver_por_nome(session, Traco, dados.get("tracos", []))
    monstro.habilidades = resolver_por_nome(session, Habilidade, dados.get("habilidades", []))
    monstro.habitats = resolver_por_nome(session, Habitat, dados.get("habitats", []))

    session.commit()
    print(f"[SEED] Monstro '{monstro.nome}' salvo (id={monstro.id}).")


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python 3_seed_monstro.py <caminho_do_json>")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    dados = json.loads(json_path.read_text(encoding="utf-8"))

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_monstro(db, dados)
    finally:
        db.close()


if __name__ == "__main__":
    main()