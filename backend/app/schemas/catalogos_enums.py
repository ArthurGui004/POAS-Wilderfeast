from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional

class CategoriaMonstro(str, Enum):
    Jovem = 'Jovem'
    Adulto = 'Adulto'
    Apex = 'Apex'

# --- DICIONÁRIOS BASE ---
class DicionarioBase(BaseModel):
    nome: str

class DicionarioOut(DicionarioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TracoOut(DicionarioOut):
    descricao: Optional[str] = None

class TecnicaOut(DicionarioOut):
    descricao: Optional[str] = None

# Relacionamentos com pontuação
class AtributoRelacionamento(BaseModel):
    id: int
    nome: str
    pontos: int
    model_config = ConfigDict(from_attributes=True)