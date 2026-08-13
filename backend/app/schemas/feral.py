class FeralBase(BaseModel):
    nome: str[cite: 1]
    titulo: Optional[str] = None[cite: 1]
    especialidade: Optional[str] = None[cite: 1]
    imagem_url: Optional[str] = None[cite: 1]
    voce_e: Optional[str] = None[cite: 1]
    tenta_ser: Optional[str] = None[cite: 1]
    feras_familiares: Optional[str] = None[cite: 1]
    prato_tipico: Optional[str] = None[cite: 1]
    tempero_tipico: Optional[str] = None[cite: 1]
    infancia_criacao: Optional[str] = None
    iniciacao_como_feral: Optional[str] = None
    ambicao: Optional[str] = None[cite: 1]
    conexao: Optional[str] = None[cite: 1]

class FeralCreate(FeralBase):
    usuario_id: int
    vigor_max: int
    vigor_atual: int

class FeralUpdate(BaseModel):
    vigor_atual: Optional[int] = None
    imagem_url: Optional[str] = None

class FeralOut(FeralBase):
    id: int[cite: 1]
    usuario_id: int
    vigor_max: int
    vigor_atual: int
    
    # Relacionamentos M:N convertidos para lista de atributos
    estilos: List[AtributoRelacionamento] = []
    habilidades: List[AtributoRelacionamento] = []
    tracos: List[TracoOut] = []
    inventario: List[InventarioFeralOut] = []

    model_config = ConfigDict(from_attributes=True)[cite: 1]