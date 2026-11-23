from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Sequence
from sqlalchemy.orm import selectinload
from app.models import Monstro, MonstroEstilo, MonstroHabilidade, MonstroParte

async def listar_monstros(db: AsyncSession) -> Sequence[Monstro]:
    query = select(Monstro)
    resultado = await db.execute(query)
    return resultado.scalars().all()

async def obter_monstro_por_id(db: AsyncSession, monstro_id: int) -> Monstro | None:
    query = select(Monstro).where(Monstro.id == monstro_id).options(
        selectinload(Monstro.estilos).selectinload(MonstroEstilo.estilo),
        selectinload(Monstro.habilidades).selectinload(MonstroHabilidade.habilidade),
        selectinload(Monstro.tracos),
        selectinload(Monstro.partes).selectinload(MonstroParte.tecnica),
    )
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()
