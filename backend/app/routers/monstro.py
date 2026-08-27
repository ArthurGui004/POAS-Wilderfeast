from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas import MonstroResponse
from app.crud import crud_monstro


router = APIRouter(prefix="/monstro", tags=["Monstros"])


@router.get("/", response_model=List[MonstroResponse])
async def listar_todos_monstros(db: AsyncSession = Depends(get_db)):
    return await crud_monstro.listar_monstros(db)


@router.get("/{monstro_id}", response_model=MonstroResponse)
async def obter_monstro_por_id(monstro_id: int, db: AsyncSession = Depends(get_db)):
    monstro = await crud_monstro.obter_monstro_por_id(db, monstro_id)
    if not monstro:
        raise HTTPException(status_code=404, detail="Monstro não encontrado.")
    return monstro