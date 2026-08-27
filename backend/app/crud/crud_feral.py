from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Sequence
from app.models import Feral
from app.schemas import FeralBase

async def criar_feral(db: AsyncSession, feral: FeralBase, usuario_id: int) -> Feral:
    novo_feral = Feral(**feral.model_dump(), usuario_id=usuario_id)
    db.add(novo_feral)
    await db.commit()
    await db.refresh(novo_feral)
    return novo_feral

async def listar_ferais_por_usuario(db: AsyncSession, usuario_id: int) -> Sequence[Feral]:
    query = select(Feral).where(Feral.usuario_id == usuario_id)
    resultado = await db.execute(query)
    return resultado.scalars().all()

async def obter_feral_por_id(db: AsyncSession, feral_id: int, usuario_id: int) -> Feral | None:
    query = select(Feral).where(Feral.id == feral_id, Feral.usuario_id == usuario_id)
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()

async def atualizar_feral(db: AsyncSession, feral: Feral, dados: FeralBase) -> Feral:
    for chave, valor in dados.model_dump(exclude_unset=True).items():
        setattr(feral, chave, valor)
    await db.commit()
    await db.refresh(feral)
    return feral

async def deletar_feral(db: AsyncSession, feral: Feral) -> None:
    await db.delete(feral)
    await db.commit()