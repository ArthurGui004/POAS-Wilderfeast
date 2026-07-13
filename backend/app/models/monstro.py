from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Monstro(Base):
    __tablename__ = "monstro"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    imagem_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    categoria: Mapped[str] = mapped_column(String(20), nullable=False)
    resistencia_base: Mapped[int] = mapped_column(Integer, nullable=False)
    resistencia_atual: Mapped[int] = mapped_column(Integer, nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    alvos: Mapped[str] = mapped_column(Text, nullable=False)
    acoes: Mapped[str] = mapped_column(Text, nullable=False)
