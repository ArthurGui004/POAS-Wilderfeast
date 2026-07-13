import os
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc
from app.database import get_db
from app.functions import get_current_user
from app.models.user import User
from app.models.feral import Feral, FeralEstilo, FeralHabilidade, Utensilio, Traco
from app.models.condicao import Condicao
from app.schemas.feral import FeralOut, CondicaoOut
from app.config import settings

router = APIRouter(prefix="/feral", tags=["ferais"])


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


FERAL_LOAD_OPTIONS = (
    selectinload(Feral.estilo),
    selectinload(Feral.habilidade),
    selectinload(Feral.utensilios),
    selectinload(Feral.tracos),
    selectinload(Feral.condicoes),
)


@router.get("/condicoes", response_model=list[CondicaoOut])
async def listar_condicoes(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Condicao))).scalars().all()


@router.get("/fichas", response_model=list[FeralOut])
async def listar_fichas(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Feral).options(*FERAL_LOAD_OPTIONS).order_by(desc(Feral.id))
    )
    return result.scalars().unique().all()


@router.get("/minhas", response_model=list[FeralOut])
async def minhas_fichas(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Feral).options(*FERAL_LOAD_OPTIONS).filter_by(player=current_user.nome)
    )
    return result.scalars().unique().all()


@router.get("/detail/{id_feral}", response_model=FeralOut)
async def detalhar_feral(id_feral: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Feral).options(*FERAL_LOAD_OPTIONS).filter_by(id=id_feral)
    )
    feral = result.scalars().unique().first()
    if not feral:
        raise HTTPException(status_code=404, detail="Feral não encontrado")
    return feral


@router.post("/create", response_model=FeralOut, status_code=201)
async def criar_feral(
    nome: str = Form(...),
    titulo: str = Form(...),
    especialidade: str = Form(...),
    voce_e: str = Form(""),
    tenta_ser: str = Form(""),
    feras_familiares: str = Form(""),
    prato_tipico: str = Form(""),
    tempero_tipico: str = Form(""),
    criacao: str = Form(...),
    iniciacao: str = Form(...),
    ambicao: str = Form(...),
    conexao: str = Form(...),
    estilo: str = Form(...),  # JSON: {ligeiro, poderoso, preciso, sagaz}
    habilidade: str = Form(...),  # JSON com as 12 habilidades
    utensilio: str = Form(...),  # JSON: {nome, alcance, ataques, durabilidade_maxima}
    tracos: str = Form(...),  # JSON: lista de 1 a 3 traços
    condicoes: str = Form("[]"),  # JSON: lista de ids
    imagem: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    estilo_data = json.loads(estilo)
    habilidade_data = json.loads(habilidade)
    utensilio_data = json.loads(utensilio)
    tracos_data = json.loads(tracos)
    condicoes_ids = json.loads(condicoes)

    feral = Feral(
        nome=nome,
        titulo=titulo,
        player=current_user.nome,
        especialidade=especialidade,
        voce_e=voce_e,
        tenta_ser=tenta_ser,
        feras_familiares=feras_familiares,
        prato_tipico=prato_tipico,
        tempero_tipico=tempero_tipico,
        criacao=criacao,
        iniciacao=iniciacao,
        ambicao=ambicao,
        conexao=conexao,
        vigor_atual=20,
        vigor_maximo=20,
        imagem_url=_salvar_imagem(imagem),
    )

    feral.estilo = FeralEstilo(**estilo_data)
    feral.habilidade = FeralHabilidade(**habilidade_data)

    dur_max = int(utensilio_data.get("durabilidade_maxima", 0))
    feral.utensilios.append(
        Utensilio(
            nome=utensilio_data["nome"],
            alcance=utensilio_data["alcance"],
            se_quebrado="0",
            durabilidade_atual=dur_max,
            durabilidade_maxima=dur_max,
            ataques=utensilio_data.get("ataques", ""),
        )
    )

    for t in tracos_data:
        feral.tracos.append(Traco(**t))

    for cid in condicoes_ids:
        cond = await db.get(Condicao, int(cid))
        if cond:
            feral.condicoes.append(cond)

    db.add(feral)
    await db.commit()

    result = await db.execute(select(Feral).options(*FERAL_LOAD_OPTIONS).filter_by(id=feral.id))
    return result.scalars().unique().first()


@router.put("/edit/{id_feral}", response_model=FeralOut)
async def editar_feral(
    id_feral: int,
    nome: str = Form(...),
    titulo: str = Form(...),
    especialidade: str = Form(...),
    criacao: str = Form(...),
    iniciacao: str = Form(...),
    ambicao: str = Form(...),
    conexao: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Feral).options(*FERAL_LOAD_OPTIONS).filter_by(id=id_feral))
    feral = result.scalars().unique().first()
    if not feral:
        raise HTTPException(status_code=404, detail="Feral não encontrado")
    if feral.player != current_user.nome:
        raise HTTPException(status_code=403, detail="Você não pode editar a ficha de outro caçador.")

    feral.nome = nome
    feral.titulo = titulo
    feral.especialidade = especialidade
    feral.criacao = criacao
    feral.iniciacao = iniciacao
    feral.ambicao = ambicao
    feral.conexao = conexao

    await db.commit()
    await db.refresh(feral)
    return feral


@router.delete("/delete/{id_feral}", status_code=204)
async def apagar_feral(
    id_feral: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    feral = await db.get(Feral, id_feral)
    if feral:
        if feral.player != current_user.nome:
            raise HTTPException(status_code=403, detail="Você não pode apagar a ficha de outro caçador.")
        await db.delete(feral)
        await db.commit()
