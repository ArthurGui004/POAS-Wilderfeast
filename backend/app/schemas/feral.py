from pydantic import BaseModel, ConfigDict


class EstiloSchema(BaseModel):
    ligeiro: int
    poderoso: int
    preciso: int
    sagaz: int

    model_config = ConfigDict(from_attributes=True)


class HabilidadeSchema(BaseModel):
    agarrar: int
    atirar: int
    curar: int
    golpear: int
    armazenar: int
    atravessar: int
    estudar: int
    manufaturar: int
    assegurar: int
    chamar: int
    exibir: int
    procurar: int

    model_config = ConfigDict(from_attributes=True)


class UtensilioSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    nome: str
    alcance: str
    se_quebrado: str = "0"
    durabilidade_atual: int
    durabilidade_maxima: int
    ataques: str | None = None


class TracoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    nome: str
    custo: str
    descricao: str
    habilidade_relacionada: str
    estilo_relacionado: str


class FeralBase(BaseModel):
    nome: str
    titulo: str
    especialidade: str
    voce_e: str | None = None
    tenta_ser: str | None = None
    feras_familiares: str | None = None
    prato_tipico: str | None = None
    tempero_tipico: str | None = None
    criacao: str
    iniciacao: str
    ambicao: str
    conexao: str


class FeralCreate(FeralBase):
    estilo: EstiloSchema
    habilidade: HabilidadeSchema
    utensilio: UtensilioSchema
    tracos: list[TracoSchema]
    condicoes: list[int] = []


class FeralUpdate(FeralBase):
    pass


class FeralOut(FeralBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    player: str
    imagem_url: str
    vigor_maximo: int
    vigor_atual: int
    estilo: EstiloSchema
    habilidade: HabilidadeSchema
    utensilios: list[UtensilioSchema]
    tracos: list[TracoSchema]


class CondicaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
