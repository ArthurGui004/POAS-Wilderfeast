class UtensilioBase(BaseModel):
    nome: str
    alcance: Optional[str] = None
    durabilidade_max: int

class UtensilioOut(UtensilioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class InventarioFeralOut(BaseModel):
    id: int
    utensilio: UtensilioOut
    durabilidade_atual: int
    se_quebrado: bool = False
    tecnicas: List[TecnicaOut] = []
    
    model_config = ConfigDict(from_attributes=True) 