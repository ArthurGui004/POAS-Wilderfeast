from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.condicao import feral_condicao


class Feral(Base):
    __tablename__ = "feral"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    player: Mapped[str] = mapped_column(Text, nullable=False)
    especialidade: Mapped[str] = mapped_column(Text, nullable=False)
    imagem_url: Mapped[str] = mapped_column(Text, nullable=False)
    vigor_maximo: Mapped[int] = mapped_column(Integer, nullable=False)
    vigor_atual: Mapped[int] = mapped_column(Integer, nullable=False)
    voce_e: Mapped[str | None] = mapped_column(String(100))
    tenta_ser: Mapped[str | None] = mapped_column(String(100))
    feras_familiares: Mapped[str | None] = mapped_column(Text)
    prato_tipico: Mapped[str | None] = mapped_column(String(50))
    tempero_tipico: Mapped[str | None] = mapped_column(String(50))
    criacao: Mapped[str] = mapped_column(Text, nullable=False)
    iniciacao: Mapped[str] = mapped_column(Text, nullable=False)
    ambicao: Mapped[str] = mapped_column(Text, nullable=False)
    conexao: Mapped[str] = mapped_column(Text, nullable=False)

    condicoes: Mapped[list["Condicao"]] = relationship(
        "Condicao", secondary=feral_condicao, back_populates="ferais"
    )
    utensilios: Mapped[list["Utensilio"]] = relationship(
        "Utensilio", back_populates="feral", cascade="all, delete-orphan"
    )
    estilo: Mapped["FeralEstilo"] = relationship(
        "FeralEstilo", back_populates="feral", uselist=False, cascade="all, delete-orphan"
    )
    habilidade: Mapped["FeralHabilidade"] = relationship(
        "FeralHabilidade", back_populates="feral", uselist=False, cascade="all, delete-orphan"
    )
    tracos: Mapped[list["Traco"]] = relationship(
        "Traco", back_populates="feral", cascade="all, delete-orphan"
    )


class Utensilio(Base):
    __tablename__ = "utensilio"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    feral_id: Mapped[int] = mapped_column(ForeignKey("feral.id", ondelete="CASCADE"))
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    alcance: Mapped[str] = mapped_column(String(50), nullable=False)
    se_quebrado: Mapped[str] = mapped_column(Text, nullable=False)
    durabilidade_atual: Mapped[int] = mapped_column(Integer, nullable=False)
    durabilidade_maxima: Mapped[int] = mapped_column(Integer, nullable=False)
    ataques: Mapped[str | None] = mapped_column(Text, nullable=True)

    feral: Mapped["Feral"] = relationship("Feral", back_populates="utensilios")


class FeralEstilo(Base):
    __tablename__ = "feral_estilo"

    feral_id: Mapped[int] = mapped_column(ForeignKey("feral.id", ondelete="CASCADE"), primary_key=True)
    ligeiro: Mapped[int] = mapped_column(Integer, nullable=False)
    poderoso: Mapped[int] = mapped_column(Integer, nullable=False)
    preciso: Mapped[int] = mapped_column(Integer, nullable=False)
    sagaz: Mapped[int] = mapped_column(Integer, nullable=False)

    feral: Mapped["Feral"] = relationship("Feral", back_populates="estilo")


class FeralHabilidade(Base):
    __tablename__ = "feral_habilidade"

    feral_id: Mapped[int] = mapped_column(ForeignKey("feral.id", ondelete="CASCADE"), primary_key=True)
    agarrar: Mapped[int] = mapped_column(Integer, nullable=False)
    atirar: Mapped[int] = mapped_column(Integer, nullable=False)
    curar: Mapped[int] = mapped_column(Integer, nullable=False)
    golpear: Mapped[int] = mapped_column(Integer, nullable=False)
    armazenar: Mapped[int] = mapped_column(Integer, nullable=False)
    atravessar: Mapped[int] = mapped_column(Integer, nullable=False)
    estudar: Mapped[int] = mapped_column(Integer, nullable=False)
    manufaturar: Mapped[int] = mapped_column(Integer, nullable=False)
    assegurar: Mapped[int] = mapped_column(Integer, nullable=False)
    chamar: Mapped[int] = mapped_column(Integer, nullable=False)
    exibir: Mapped[int] = mapped_column(Integer, nullable=False)
    procurar: Mapped[int] = mapped_column(Integer, nullable=False)

    feral: Mapped["Feral"] = relationship("Feral", back_populates="habilidade")


class Traco(Base):
    __tablename__ = "traco_feral"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    feral_id: Mapped[int] = mapped_column(ForeignKey("feral.id", ondelete="CASCADE"))
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    custo: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    habilidade_relacionada: Mapped[str] = mapped_column(String(50), nullable=False)
    estilo_relacionado: Mapped[str] = mapped_column(String(50), nullable=False)

    feral: Mapped["Feral"] = relationship("Feral", back_populates="tracos")
