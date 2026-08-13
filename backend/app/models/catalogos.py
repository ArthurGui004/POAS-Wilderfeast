from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Traco(Base):
    __tablename__ = 'traco'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)

class Estilo(Base):
    __tablename__ = 'estilo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False)

class Habilidade(Base):
    __tablename__ = 'habilidade'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), nullable=False)

class Tecnica(Base):
    __tablename__ = 'tecnica'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)