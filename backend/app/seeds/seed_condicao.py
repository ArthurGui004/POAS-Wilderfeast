import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal, engine
from app.models.condicao import Condicao

CONDICOES_PADRAO = [
    "Amedrontado", "Atordoado", "Confuso", "Convalescente", "Descansado",
    "Dissonante", "Envenenado", "Escondido", "Expandido", "Exposto",
    "Fadigado", "Ferido", "Preso", "Queimado", "Revigorado",
]


async def criar_condicoes_padrao() -> None:
    unicas = list(dict.fromkeys(CONDICOES_PADRAO))

    async with AsyncSessionLocal() as db:
        existentes = set((await db.execute(select(Condicao.nome))).scalars().all())
        novas = [Condicao(nome=n) for n in unicas if n not in existentes]
        if novas:
            db.add_all(novas)
            await db.commit()

    print(f"  Condições: {len(novas)} inserida(s), {len(unicas) - len(novas)} já existiam.")


async def _main() -> None:
    try:
        await criar_condicoes_padrao()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())