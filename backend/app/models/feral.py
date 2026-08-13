# models/feral.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

# Tabela de Associação N:N pura
feral_traco_assoc = Table(
    'feral_traco', Base.metadata,
    Column('feral_id', Integer, ForeignKey('feral.id', ondelete="CASCADE"), primary_key=True),
    Column('traco_id', Integer, ForeignKey('traco.id', ondelete="CASCADE"), primary_key=True)
)

class Feral(Base):
    __tablename__ = 'feral'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete="CASCADE"), nullable=False)
    nome = Column(String(100), nullable=False)
    titulo = Column(String(100))
    especialidade = Column(String(100))
    imagem_url = Column(String(255))
    vigor_max = Column(Integer, nullable=False)
    vigor_atual = Column(Integer, nullable=False)
    voce_e = Column(Text)
    tenta_ser = Column(Text)
    feras_familiares = Column(Text)
    prato_tipico = Column(String(100))
    tempero_tipico = Column(String(100))
    infancia_criacao = Column(Text)
    iniciacao_como_feral = Column(Text)
    ambicao = Column(Text)
    conexao = Column(Text)
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="ferais")
    estilos = relationship("FeralEstilo", back_populates="feral", cascade="all, delete-orphan")
    habilidades = relationship("FeralHabilidade", back_populates="feral", cascade="all, delete-orphan")
    tracos = relationship("Traco", secondary=feral_traco_assoc)
    inventario = relationship("FeralInventario", back_populates="feral", cascade="all, delete-orphan")

# Classes de Associação com colunas extras
class FeralEstilo(Base):
    __tablename__ = 'feral_estilo'
    feral_id = Column(Integer, ForeignKey('feral.id', ondelete="CASCADE"), primary_key=True)
    estilo_id = Column(Integer, ForeignKey('estilo.id', ondelete="CASCADE"), primary_key=True)
    pontos = Column(Integer, default=0)
    
    feral = relationship("Feral", back_populates="estilos")
    estilo = relationship("Estilo")

class FeralHabilidade(Base):
    __tablename__ = 'feral_habilidade'
    feral_id = Column(Integer, ForeignKey('feral.id', ondelete="CASCADE"), primary_key=True)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete="CASCADE"), primary_key=True)
    pontos = Column(Integer, default=0)
    
    feral = relationship("Feral", back_populates="habilidades")
    habilidade = relationship("Habilidade")