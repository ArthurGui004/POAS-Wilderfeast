import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.monstro import Monstro
from app.schemas.monstro import MonstroOut
from app.config import settings

router = APIRouter(prefix="/bestiario", tags=["bestiário"])


def _salvar_imagem(imagem: UploadFile | None) -> str:
    if not imagem or not imagem.filename:
        return ""
    ext = os.path.splitext(imagem.filename)[1]
    nome_arquivo = f"{uuid.uuid4().hex}{ext}"
    caminho = os.path.join(settings.UPLOAD_DIR, nome_arquivo)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(imagem.file.read())
    return nome_arquivo


@router.get("/", response_model=list[MonstroOut])
async def listar_monstros(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Monstro))).scalars().all()


@router.get("/{id_besta}", response_model=MonstroOut)
async def detalhar_monstro(id_besta: int, db: AsyncSession = Depends(get_db)):
    monstro = await db.get(Monstro, id_besta)
    if not monstro:
        raise HTTPException(status_code=404, detail="Besta não encontrada")
    return monstro


@router.post("/", response_model=MonstroOut, status_code=201)
async def criar_monstro(
    nome: str = Form(...),
    categoria: str = Form(...),
    resistencia_base: int = Form(...),
    descricao: str = Form(...),
    alvos: str = Form(...),
    acoes: str = Form(...),
    imagem: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    monstro = Monstro(
        nome=nome,
        categoria=categoria,
        resistencia_base=resistencia_base,
        resistencia_atual=resistencia_base,
        descricao=descricao,
        alvos=alvos,
        acoes=acoes,
        imagem_url=_salvar_imagem(imagem),
    )
    db.add(monstro)
    await db.commit()
    await db.refresh(monstro)
    return monstro


@router.put("/{id_besta}", response_model=MonstroOut)
async def editar_monstro(
    id_besta: int,
    nome: str = Form(...),
    categoria: str = Form(...),
    resistencia_base: int = Form(...),
    descricao: str = Form(...),
    alvos: str = Form(...),
    acoes: str = Form(...),
    imagem: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    monstro = await db.get(Monstro, id_besta)
    if not monstro:
        raise HTTPException(status_code=404, detail="Besta não encontrada")

    monstro.nome = nome
    monstro.categoria = categoria
    monstro.resistencia_base = resistencia_base
    monstro.descricao = descricao
    monstro.alvos = alvos
    monstro.acoes = acoes
    nova_imagem = _salvar_imagem(imagem)
    if nova_imagem:
        monstro.imagem_url = nova_imagem

    await db.commit()
    await db.refresh(monstro)
    return monstro


@router.delete("/{id_besta}", status_code=204)
async def apagar_monstro(id_besta: int, db: AsyncSession = Depends(get_db)):
    monstro = await db.get(Monstro, id_besta)
    if monstro:
        await db.delete(monstro)
        await db.commit()
