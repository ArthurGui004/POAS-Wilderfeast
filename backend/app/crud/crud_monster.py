from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Sequence
from app.models import Monstro

async def listar_monstros(db: AsyncSession) -> Sequence[Monstro]:
    query = select(Monstro)
    resultado = await db.execute(query)
    return resultado.scalars().all()

async def obter_monstro_por_id(db: AsyncSession, monstro_id: int) -> Monstro | None:
    query = select(Monstro).where(Monstro.id == monstro_id)
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()