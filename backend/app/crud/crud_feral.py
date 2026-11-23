from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Sequence
from app.models import Feral, FeralInventario, Utensilio
from app.models.utensilio import catalogo_disponivel
from app.schemas import FeralBase, FeralCreate

async def criar_feral(db: AsyncSession, feral: FeralCreate, usuario_id: int) -> Feral | None:
    utensilio = await db.scalar(catalogo_disponivel(usuario_id).where(Utensilio.id == feral.utensilio_id).with_for_update())
    if utensilio is None:
        return None
    item = FeralInventario(utensilio=utensilio, durabilidade_atual=utensilio.durabilidade_max,
                           se_quebrado=utensilio.durabilidade_max == 0)
    novo_feral = Feral(**feral.model_dump(exclude={"utensilio_id"}), usuario_id=usuario_id, inventario=[item])
    db.add(novo_feral)
    await db.commit()
    await db.refresh(novo_feral)
    return novo_feral

async def listar_ferais_por_usuario(db: AsyncSession, usuario_id: int) -> Sequence[Feral]:
    query = select(Feral).where(Feral.usuario_id == usuario_id)
    resultado = await db.execute(query)
    return resultado.scalars().all()

async def obter_feral_por_id(db: AsyncSession, feral_id: int, usuario_id: int, *, com_inventario: bool = False) -> Feral | None:
    query = select(Feral).where(Feral.id == feral_id, Feral.usuario_id == usuario_id)
    if com_inventario:
        query = query.options(selectinload(Feral.inventario).joinedload(FeralInventario.utensilio))
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
