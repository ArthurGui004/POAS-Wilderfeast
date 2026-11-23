from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, PositiveInt, StringConstraints
from sqlalchemy import and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user, get_current_user_optional
from app.models import Estilo, Feral, FeralEstilo, FeralHabilidade, FeralInventario, Habilidade, Traco, Usuario, Utensilio
from app.models.condicao import Condicao, feral_condicao
from app.models.feral import ItemEncontrado, feral_traco_assoc
from app.models.utensilio import catalogo_disponivel
from app.schemas.catalogos_enums import TecnicaResponse
from app.schemas.utensilio import UtensilioResponse

router = APIRouter(tags=["Equipamento e atributos"])
Database = Annotated[AsyncSession, Depends(get_db)]


async def feral_da_sessao(feral_id: int, db: Database, usuario: Usuario = Depends(get_current_user)):
    feral = await db.scalar(select(Feral).where(
        Feral.id == feral_id, Feral.usuario_id == usuario.id
    ).with_for_update())
    if feral is None:
        raise HTTPException(404, "Feral não encontrado.")
    return feral


Ficha = Annotated[Feral, Depends(feral_da_sessao)]


class Ferramenta(UtensilioResponse):
    tecnicas: list[TecnicaResponse]


class Item(BaseModel, from_attributes=True):
    id: int
    utensilio: Ferramenta
    durabilidade_atual: int
    estilo_escolhido: str | None
    se_quebrado: bool | None
    tecnicas: list[TecnicaResponse]


class Desgaste(BaseModel):
    durabilidade_atual: int = Field(ge=0)


class EstiloEscolhido(BaseModel):
    estilo_escolhido: Annotated[str, StringConstraints(min_length=1, max_length=100)]


QUANTIDADE_MAXIMA = 2_147_483_647


class NovoItemEncontrado(BaseModel):
    nome: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    quantidade: int = Field(default=1, strict=True, ge=1, le=QUANTIDADE_MAXIMA)
    descricao: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None = None


class ItemEncontradoResponse(NovoItemEncontrado, from_attributes=True):
    id: int


class EdicaoItemEncontrado(NovoItemEncontrado):
    quantidade: int = Field(default=1, strict=True, ge=0, le=QUANTIDADE_MAXIMA)


class AjusteQuantidade(BaseModel):
    variacao: Literal[-1, 1]


@router.get("/feral/{feral_id}/itens-encontrados", response_model=list[ItemEncontradoResponse])
async def listar_itens_encontrados(feral: Ficha, db: Database):
    consulta = select(ItemEncontrado).where(ItemEncontrado.feral_id == feral.id).order_by(ItemEncontrado.id)
    return (await db.scalars(consulta)).all()


@router.post("/feral/{feral_id}/itens-encontrados", response_model=ItemEncontradoResponse, status_code=201)
async def adicionar_item_encontrado(dados: NovoItemEncontrado, feral: Ficha, db: Database):
    item = ItemEncontrado(
        feral_id=feral.id,
        nome=dados.nome,
        quantidade=dados.quantidade,
        descricao=dados.descricao or None,
    )
    db.add(item)
    await db.commit()
    return item


def item_encontrado_da_ficha(feral: Feral, item_id: int):
    return (ItemEncontrado.feral_id == feral.id, ItemEncontrado.id == item_id)


@router.put(
    "/feral/{feral_id}/itens-encontrados/{item_id}", response_model=ItemEncontradoResponse,
    responses={204: {"description": "Item removido ao chegar a zero"}},
)
async def editar_item_encontrado(item_id: int, dados: EdicaoItemEncontrado, feral: Ficha, db: Database):
    if dados.quantidade == 0:
        removido = await db.scalar(delete(ItemEncontrado).where(
            *item_encontrado_da_ficha(feral, item_id)
        ).returning(ItemEncontrado.id))
        if removido is None:
            raise HTTPException(404, "Item não encontrado nesta ficha.")
        await db.commit()
        return Response(status_code=204)

    item = await db.scalar(select(ItemEncontrado).where(*item_encontrado_da_ficha(feral, item_id)))
    if item is None:
        raise HTTPException(404, "Item não encontrado nesta ficha.")
    item.nome = dados.nome
    item.quantidade = dados.quantidade
    item.descricao = dados.descricao or None
    await db.commit()
    return item


@router.patch(
    "/feral/{feral_id}/itens-encontrados/{item_id}", response_model=ItemEncontradoResponse,
    responses={204: {"description": "Item removido ao chegar a zero"}},
)
async def ajustar_quantidade_encontrada(item_id: int, dados: AjusteQuantidade, feral: Ficha, db: Database):
    escopo = item_encontrado_da_ficha(feral, item_id)
    quantidade = ItemEncontrado.quantidade
    dentro_do_limite = quantidade < QUANTIDADE_MAXIMA if dados.variacao == 1 else quantidade > 1
    item = await db.scalar(update(ItemEncontrado).where(
        *escopo, dentro_do_limite
    ).values(quantidade=quantidade + dados.variacao).returning(ItemEncontrado))
    if item is None:
        if dados.variacao == -1:
            removido = await db.scalar(delete(ItemEncontrado).where(
                *escopo, quantidade == 1
            ).returning(ItemEncontrado.id))
            if removido is not None:
                await db.commit()
                return Response(status_code=204)
        if await db.scalar(select(ItemEncontrado.id).where(*escopo)) is None:
            raise HTTPException(404, "Item não encontrado nesta ficha.")
        raise HTTPException(409, "A quantidade já está no limite permitido.")
    await db.commit()
    return item


@router.get("/utensilio/", response_model=list[Ferramenta])
async def catalogo(db: Database, response: Response, usuario: Usuario | None = Depends(get_current_user_optional)):
    response.headers["Cache-Control"] = "private, no-store"
    consulta = catalogo_disponivel(usuario.id if usuario else None).options(
        selectinload(Utensilio.tecnicas)
    ).order_by(Utensilio.nome, Utensilio.id)
    return (await db.scalars(consulta)).all()


def itens_da_ficha(feral: Feral):
    return select(FeralInventario).where(FeralInventario.feral_id == feral.id).options(
        selectinload(FeralInventario.utensilio).selectinload(Utensilio.tecnicas),
        selectinload(FeralInventario.tecnicas),
    )


@router.get("/feral/{feral_id}/inventario", response_model=list[Item])
async def inventario(feral: Ficha, db: Database):
    return (await db.scalars(itens_da_ficha(feral).order_by(FeralInventario.id))).all()


async def item_da_ficha(item_id: int, feral: Ficha, db: Database):
    item = await db.scalar(itens_da_ficha(feral).where(FeralInventario.id == item_id))
    if item is None:
        raise HTTPException(404, "Item não encontrado nesta ficha.")
    return item


@router.put("/feral/{feral_id}/inventario/{item_id}", response_model=Item)
async def ajustar(dados: Desgaste, db: Database, item: FeralInventario = Depends(item_da_ficha)):
    if dados.durabilidade_atual > item.utensilio.durabilidade_max:
        raise HTTPException(422, "A durabilidade atual supera o máximo do utensílio.")
    item.durabilidade_atual = dados.durabilidade_atual
    item.se_quebrado = item.durabilidade_atual == 0
    await db.commit()
    return item


@router.put("/feral/{feral_id}/inventario/{item_id}/estilo", response_model=Item)
async def escolher_estilo(dados: EstiloEscolhido, db: Database, item: FeralInventario = Depends(item_da_ficha)):
    if dados.estilo_escolhido not in (item.utensilio.estilos_principais or []):
        raise HTTPException(422, "Escolha um dos estilos principais deste utensílio.")
    item.estilo_escolhido = dados.estilo_escolhido
    await db.commit()
    return item


Grupo = Literal["estilos", "habilidades", "tracos", "condicoes"]
GRUPOS = {
    "estilos": (Estilo, FeralEstilo.__table__, "estilo_id"),
    "habilidades": (Habilidade, FeralHabilidade.__table__, "habilidade_id"),
    "tracos": (Traco, feral_traco_assoc, "traco_id"),
    "condicoes": (Condicao, feral_condicao, "condicao_id"),
}


class Atributo(BaseModel):
    id: int
    nome: str
    valor: int
    descricao: str | None = None


class Ajuste(BaseModel):
    grupo: Grupo
    id: PositiveInt
    valor: int = Field(ge=0, le=2147483647)


@router.get("/feral/{feral_id}/atributos", response_model=dict[Grupo, list[Atributo]])
async def atributos(feral: Ficha, db: Database):
    resposta = {}
    for grupo, (modelo, tabela, chave) in GRUPOS.items():
        valor = tabela.c.pontos if "pontos" in tabela.c else tabela.c.feral_id.is_not(None)
        consulta = select(modelo, valor).outerjoin(tabela, and_(
            tabela.c[chave] == modelo.id, tabela.c.feral_id == feral.id
        )).order_by(modelo.nome, modelo.id)
        resposta[grupo] = [
            Atributo(id=obj.id, nome=obj.nome, valor=int(pontos or 0),
                     descricao=getattr(obj, "descricao", None))
            for obj, pontos in await db.execute(consulta)
        ]
    return resposta


@router.put("/feral/{feral_id}/atributos", response_model=Ajuste)
async def ajustar_atributo(dados: Ajuste, feral: Ficha, db: Database):
    modelo, tabela, chave = GRUPOS[dados.grupo]
    if await db.get(modelo, dados.id) is None:
        raise HTTPException(404, "Atributo não encontrado.")
    tem_pontos = "pontos" in tabela.c
    if not tem_pontos and dados.valor > 1:
        raise HTTPException(422, "Traços e condições aceitam apenas 0 ou 1.")
    await db.execute(delete(tabela).where(tabela.c.feral_id == feral.id, tabela.c[chave] == dados.id))
    if dados.valor:
        campos = {"feral_id": feral.id, chave: dados.id}
        if tem_pontos:
            campos["pontos"] = dados.valor
        await db.execute(tabela.insert().values(**campos))
    await db.commit()
    return dados
