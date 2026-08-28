import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Monstro, Traco, Habilidade, Habitat

def resolver_por_nomes(session: Session, model, nomes: list[str]):
    if not nomes:
        return []
    # Busca todos de uma vez usando IN_ em vez de loop N+1
    stmt = select(model).where(model.nome.in_(nomes))
    encontrados = session.scalars(stmt).all()
    
    nomes_encontrados = {obj.nome for obj in encontrados}
    for nome in nomes:
        if nome not in nomes_encontrados:
            print(f"  [AVISO] {model.__name__} '{nome}' não encontrado no banco — pulando.")
    return encontrados

def executar_seed(json_path: Path) -> None:
    dados = json.loads(json_path.read_text(encoding="utf-8"))
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as db:
        stmt = select(Monstro).where(Monstro.nome == dados["nome"])
        monstro = db.scalars(stmt).first()
        
        if not monstro:
            monstro = Monstro(nome=dados["nome"])
            db.add(monstro)

        monstro.dieta = dados.get("dieta")
        monstro.comportamento = dados.get("comportamento")
        monstro.descricao = dados.get("descricao")

        monstro.tracos = resolver_por_nomes(db, Traco, dados.get("tracos", []))
        monstro.habilidades = resolver_por_nomes(db, Habilidade, dados.get("habilidades", []))
        monstro.habitats = resolver_por_nomes(db, Habitat, dados.get("habitats", []))

        db.commit()
        print(f"[SEED] Monstro '{monstro.nome}' salvo.")