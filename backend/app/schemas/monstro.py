from pydantic import BaseModel, ConfigDict


class MonstroBase(BaseModel):
    nome: str
    categoria: str
    resistencia_base: int
    descricao: str
    alvos: str
    acoes: str


class MonstroCreate(MonstroBase):
    pass


class MonstroUpdate(MonstroBase):
    resistencia_atual: int | None = None


class MonstroOut(MonstroBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    imagem_url: str | None = None
    resistencia_atual: int
