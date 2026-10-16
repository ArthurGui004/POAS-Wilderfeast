import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal, engine
from app.models.catalogos import Habilidade

HABILIDADES_PADRAO = [
    "AGARRAR", "ARMAZENAR", "ASSEGURAR",
    "ATIRAR", "ATRAVESSAR", "CHAMAR",
    "CURAR", "ESTUDAR", "EXIBIR",
    "GOLPEAR", "MANUFATURAR", "PROCURAR",
]


async def criar_habilidades_padrao() -> None:
    unicas = list(dict.fromkeys(HABILIDADES_PADRAO))

    async with AsyncSessionLocal() as db:
        existentes = set((await db.execute(select(Habilidade.nome))).scalars().all())
        novas = [Habilidade(nome=n) for n in unicas if n not in existentes]
        if novas:
            db.add_all(novas)
            await db.commit()

    print(f"  Habilidades: {len(novas)} inserida(s), {len(unicas) - len(novas)} já existiam.")


async def _main() -> None:
    try:
        await criar_habilidades_padrao()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())