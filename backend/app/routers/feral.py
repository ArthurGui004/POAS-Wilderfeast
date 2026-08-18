from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.deps import get_current_user
from app.models import Usuario, Feral
from app.schemas import FeralBase, FeralResponse

router = APIRouter(prefix="/feral", tags=["Feral"])


@router.post("/", response_model=FeralResponse, status_code=status.HTTP_201_CREATED)
async def criar_feral(
    feral: FeralBase,
    usuario_atual: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    novo_feral = Feral(**feral.model_dump(), usuario_id=usuario_atual.id)
    db.add(novo_feral)
    await db.commit()
    await db.refresh(novo_feral)
    return novo_feral

@router.get("/meus", response_model=List[FeralResponse])
async def listar_meus_ferais(
    usuario_atual: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Feral).where(Feral.usuario_id == usuario_atual.id)
    resultado = await db.execute(query)
    return resultado.scalars().all()



@router.get("/{feral_id}", response_model=FeralResponse)
async def obter_feral(
    feral_id: int,
    usuario_atual: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Feral).where(
        Feral.id == feral_id, 
        Feral.usuario_id == usuario_atual.id
    )
    resultado = await db.execute(query)
    feral = resultado.scalar_one_or_none()
    
    if not feral:
        raise HTTPException(status_code=404, detail="Feral não encontrado.")
    return feral



@router.put("/{feral_id}", response_model=FeralResponse)
async def editar_feral(
    feral_id: int,
    dados: FeralBase,
    usuario_atual: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Feral).where(
        Feral.id == feral_id, 
        Feral.usuario_id == usuario_atual.id
    )
    resultado = await db.execute(query)
    feral = resultado.scalar_one_or_none()
    
    if not feral:
        raise HTTPException(status_code=404, detail="Feral não encontrado.")
    
    for chave, valor in dados.model_dump(exclude_unset=True).items():
        setattr(feral, chave, valor)
        
    await db.commit()
    await db.refresh(feral)
    return feral



@router.delete("/{feral_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_feral(
    feral_id: int,
    usuario_atual: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Feral).where(
        Feral.id == feral_id, 
        Feral.usuario_id == usuario_atual.id
    )
    resultado = await db.execute(query)
    feral = resultado.scalar_one_or_none()
    
    if not feral:
        raise HTTPException(status_code=404, detail="Feral não encontrado.")
    
    await db.delete(feral)
    await db.commit()
    return None