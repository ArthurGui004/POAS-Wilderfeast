from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.condicao import Condicao

CONDICOES_PADRAO = [
    "Amedrontado", "Atordoado", "Confuso", "Convalescente", "Descansado",
    "Dissonante", "Envenenado", "Escondido", "Expandido", "Exposto",
    "Fadigado", "Ferido", "Preso", "Queimado", "Revigorado",
]


async def criar_condicoes_padrao():
    async with AsyncSessionLocal() as db:
        existentes = (await db.execute(select(Condicao.nome))).scalars().all()
        novas = [Condicao(nome=n) for n in CONDICOES_PADRAO if n not in existentes]
        if novas:
            db.add_all(novas)
            await db.commit()
