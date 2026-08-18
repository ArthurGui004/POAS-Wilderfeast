from pydantic import BaseModel, ConfigDict
from typing import Optional
from enums import CategoriaMonstro 


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
    model_config = ConfigDict(from_attributes=True)


# --- PARTES DO MONSTRO ---
class MonstroParteBase(BaseModel):
    nome: str
    alcance: Optional[str] = None
    durabilidade_max: int
    durabilidade_atual: int
    se_quebrado: bool = False

class MonstroParteCreate(MonstroParteBase):
    monstro_id: int
    tecnica_id: int

class MonstroParteResponse(MonstroParteBase):
    id: int
    monstro_id: int
    tecnica_id: int
    model_config = ConfigDict(from_attributes=True)