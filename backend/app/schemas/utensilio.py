from pydantic import BaseModel, ConfigDict
from typing import Optional


# --- UTENSÍLIO ---
class UtensilioBase(BaseModel):
    nome: str
    alcance: Optional[str] = None
    durabilidade_max: int

class UtensilioCreate(UtensilioBase):
    pass

class UtensilioResponse(UtensilioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- INVENTÁRIO DO FERAL ---
class FeralInventarioBase(BaseModel):
    durabilidade_atual: int
    se_quebrado: bool = False

class FeralInventarioCreate(FeralInventarioBase):
    feral_id: int
    utensilio_id: int

class FeralInventarioResponse(FeralInventarioBase):
    id: int
    feral_id: int
    utensilio_id: int
    model_config = ConfigDict(from_attributes=True)