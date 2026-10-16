import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal, engine
from app.models.catalogos import Estilo

ESTILO_PADRAO = [
    "PODEROSO", "LIGEIRO", "PRECISO", "SAGAZ",
]


async def criar_estilos_padrao() -> None:
    unicos = list(dict.fromkeys(ESTILO_PADRAO))

    async with AsyncSessionLocal() as db:
        existentes = set((await db.execute(select(Estilo.nome))).scalars().all())
        novos = [Estilo(nome=n) for n in unicos if n not in existentes]
        if novos:
            db.add_all(novos)
            await db.commit()

    print(f"  Estilos: {len(novos)} inserido(s), {len(unicos) - len(novos)} já existiam.")


async def _main() -> None:
    try:
        await criar_estilos_padrao()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())