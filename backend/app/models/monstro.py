# models/monstro.py
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from enums import CategoriaMonstro

monstro_traco_assoc = Table(
    'monstro_traco', Base.metadata,
    Column('monstro_id', Integer, ForeignKey('monstro.id', ondelete="CASCADE"), primary_key=True),
    Column('traco_id', Integer, ForeignKey('traco.id', ondelete="CASCADE"), primary_key=True)
)

class Monstro(Base):
    __tablename__ = 'monstro'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    categoria = Column(SQLEnum(CategoriaMonstro), nullable=False)
    vigor_base = Column(Integer, nullable=False)
    vigor_atual = Column(Integer, nullable=False)
    historia = Column(Text)
    alvos = Column(Text)
    dieta = Column(String(100))
    habitat = Column(String(100))
    
    estilos = relationship("MonstroEstilo", back_populates="monstro", cascade="all, delete-orphan")
    habilidades = relationship("MonstroHabilidade", back_populates="monstro", cascade="all, delete-orphan")
    tracos = relationship("Traco", secondary=monstro_traco_assoc)
    partes = relationship("MonstroParte", back_populates="monstro", cascade="all, delete-orphan")

class MonstroEstilo(Base):
    __tablename__ = 'monstro_estilo'
    monstro_id = Column(Integer, ForeignKey('monstro.id', ondelete="CASCADE"), primary_key=True)
    estilo_id = Column(Integer, ForeignKey('estilo.id', ondelete="CASCADE"), primary_key=True)
    pontos = Column(Integer, default=0)
    
    monstro = relationship("Monstro", back_populates="estilos")
    estilo = relationship("Estilo")

class MonstroHabilidade(Base):
    __tablename__ = 'monstro_habilidade'
    monstro_id = Column(Integer, ForeignKey('monstro.id', ondelete="CASCADE"), primary_key=True)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete="CASCADE"), primary_key=True)
    pontos = Column(Integer, default=0)
    
    monstro = relationship("Monstro", back_populates="habilidades")
    habilidade = relationship("Habilidade")

class MonstroParte(Base):
    __tablename__ = 'monstro_parte'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    monstro_id = Column(Integer, ForeignKey('monstro.id', ondelete="CASCADE"), nullable=False)
    tecnica_id = Column(Integer, ForeignKey('tecnica.id', ondelete="RESTRICT"), nullable=False)
    nome = Column(String(100), nullable=False)
    alcance = Column(String(50))
    durabilidade_max = Column(Integer, nullable=False)
    durabilidade_atual = Column(Integer, nullable=False)
    se_quebrado = Column(Boolean, default=False)
    
    monstro = relationship("Monstro", back_populates="partes")
    tecnica = relationship("Tecnica")