# schemas/catalogos.py
from pydantic import BaseModel, ConfigDict
from typing import Optional


# --- TRAÇO ---
class TracoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None

class TracoCreate(TracoBase):
    pass

class TracoResponse(TracoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)



# --- ESTILO ---
class EstiloBase(BaseModel):
    nome: str

class EstiloCreate(EstiloBase):
    pass

class EstiloResponse(EstiloBase):
    id: int
    model_config = ConfigDict(from_attributes=True)



# --- HABILIDADE ---
class HabilidadeBase(BaseModel):
    nome: str

class HabilidadeCreate(HabilidadeBase):
    pass

class HabilidadeResponse(HabilidadeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)



# --- TÉCNICA ---
class TecnicaBase(BaseModel):
    nome: str
    descricao: Optional[str] = None

class TecnicaCreate(TecnicaBase):
    pass

class TecnicaResponse(TecnicaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)