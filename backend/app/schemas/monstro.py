from pydantic import AliasPath, BaseModel, ConfigDict, Field
from app.schemas.catalogos_enums import TecnicaResponse, TracoResponse
from typing import Optional
from app.enums import CategoriaMonstro 


# --- MONSTRO ---
class MonstroBase(BaseModel):
    nome: str
    categoria: CategoriaMonstro
    vigor_base: int
    vigor_atual: int
    historia: Optional[str] = None
    alvos: Optional[str] = None
    dieta: Optional[str] = None
    habitat: Optional[str] = None

class MonstroCreate(MonstroBase):
    pass

class MonstroResponse(MonstroBase):
    id: int
    comportamento: str | None = None
    imagem_url: str | None = None
    model_config = ConfigDict(from_attributes=True)


# --- PARTES DO MONSTRO ---
class MonstroParteBase(BaseModel):
    nome: str
    alcance: Optional[str] = None
    durabilidade_max: int
    durabilidade_atual: int
    se_quebrado: str | None = None

class MonstroParteCreate(MonstroParteBase):
    monstro_id: int
    tecnica_id: int

class MonstroParteResponse(MonstroParteBase):
    id: int
    monstro_id: int
    tecnica_id: int
    model_config = ConfigDict(from_attributes=True)
    tecnica: TecnicaResponse


class EstiloDaFera(BaseModel, from_attributes=True):
    nome: str = Field(validation_alias=AliasPath("estilo", "nome"))
    pontos: int | None


class HabilidadeDaFera(BaseModel, from_attributes=True):
    nome: str = Field(validation_alias=AliasPath("habilidade", "nome"))
    pontos: int | None


class MonstroDetalhado(MonstroResponse):
    estilos: list[EstiloDaFera]
    habilidades: list[HabilidadeDaFera]
    tracos: list[TracoResponse]
    partes: list[MonstroParteResponse]
