# schemas/feral.py
from pydantic import AliasPath, BaseModel, ConfigDict, Field, PositiveInt
from typing import Optional

class FeralBase(BaseModel):
    nome: str
    titulo: Optional[str] = None
    especialidade: Optional[str] = None
    imagem_url: Optional[str] = None
    vigor_max: int
    vigor_atual: int
    voce_e: Optional[str] = None
    tenta_ser: Optional[str] = None
    feras_familiares: Optional[str] = None
    prato_tipico: Optional[str] = None
    tempero_tipico: Optional[str] = None
    infancia_criacao: Optional[str] = None
    iniciacao_como_feral: Optional[str] = None
    ambicao: Optional[str] = None
    conexao: Optional[str] = None

class FeralCreate(FeralBase):
    utensilio_id: PositiveInt

class FeralResponse(FeralBase):
    id: int
    usuario_id: int
    model_config = ConfigDict(from_attributes=True)


class ItemDaFicha(BaseModel, from_attributes=True):
    id: int
    nome: str = Field(validation_alias=AliasPath("utensilio", "nome"))


class FeralDetalhado(FeralResponse):
    inventario: list[ItemDaFicha]
