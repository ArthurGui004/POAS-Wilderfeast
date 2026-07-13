from sqlalchemy import String, Table, Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

feral_condicao = Table(
    "feral_condicao",
    Base.metadata,
    Column("feral_id", Integer, ForeignKey("feral.id", ondelete="CASCADE"), primary_key=True),
    Column("condicao_id", Integer, ForeignKey("condicao.id", ondelete="CASCADE"), primary_key=True),
)


class Condicao(Base):
    __tablename__ = "condicao"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    ferais: Mapped[list["Feral"]] = relationship(
        "Feral", secondary=feral_condicao, back_populates="condicoes"
    )
