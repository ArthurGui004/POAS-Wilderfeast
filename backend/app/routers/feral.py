from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.deps import get_current_user
from app.models import Usuario
from app.schemas import FeralBase, FeralResponse
from app.crud import crud_feral

router = APIRouter(prefix="/feral", tags=["Feral"])

@router.post("/", response_model=FeralResponse, status_code=status.HTTP_201_CREATED)
async def criar_feral(feral: FeralBase, usuario_atual: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await crud_feral.criar_feral(db, feral, usuario_atual.id)


@router.get("/meus", response_model=List[FeralResponse])
async def listar_meus_ferais(usuario_atual: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await crud_feral.listar_ferais_por_usuario(db, usuario_atual.id)


@router.get("/{feral_id}", response_model=FeralResponse)
async def obter_feral(feral_id: int, usuario_atual: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    feral = await crud_feral.obter_feral_por_id(db, feral_id, usuario_atual.id)
    if not feral:
        raise HTTPException(status_code=404, detail="Feral não encontrado.")
    return feral


@router.put("/{feral_id}", response_model=FeralResponse)
async def editar_feral(feral_id: int, dados: FeralBase, usuario_atual: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    feral = await crud_feral.obter_feral_por_id(db, feral_id, usuario_atual.id)
    if not feral:
        raise HTTPException(status_code=404, detail="Feral não encontrado.")
    return await crud_feral.atualizar_feral(db, feral, dados)


@router.delete("/{feral_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_feral(feral_id: int, usuario_atual: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    feral = await crud_feral.obter_feral_por_id(db, feral_id, usuario_atual.id)
    if not feral:
        raise HTTPException(status_code=404, detail="Feral não encontrado.")
    await crud_feral.deletar_feral(db, feral)
    return None