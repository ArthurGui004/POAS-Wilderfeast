from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import Monstro
from app.schemas import MonstroResponse

router = APIRouter(prefix="/monstro", tags=["Monstros"])

@router.get("/", response_model=List[MonstroResponse])
async def listar_todos_monstros(db: AsyncSession = Depends(get_db)):
    query = select(Monstro)
    resultado = await db.execute(query)
    return resultado.scalars().all()

@router.get("/{monstro_id}", response_model=MonstroResponse)
async def obter_monstro_por_id(monstro_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Monstro).where(Monstro.id == monstro_id)
    resultado = await db.execute(query)
    monstro = resultado.scalar_one_or_none()
    
    if not monstro:
        raise HTTPException(status_code=404, detail="Monstro não encontrado.")
    return monstro