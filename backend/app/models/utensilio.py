from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base

utensilio_tecnica_assoc = Table(
    'utensilio_tecnica', Base.metadata,
    Column('utensilio_id', Integer, ForeignKey('utensilio.id', ondelete="CASCADE"), primary_key=True),
    Column('tecnica_id', Integer, ForeignKey('tecnica.id', ondelete="CASCADE"), primary_key=True)
)

feral_inventario_tecnica_assoc = Table(
    'feral_inventario_tecnica', Base.metadata,
    Column('feral_inventario_id', Integer, ForeignKey('feral_inventario.id', ondelete="CASCADE"), primary_key=True),
    Column('tecnica_id', Integer, ForeignKey('tecnica.id', ondelete="CASCADE"), primary_key=True)
)

class Utensilio(Base):
    __tablename__ = 'utensilio'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    alcance = Column(String(50))
    durabilidade_max = Column(Integer, nullable=False)
    
    tecnicas = relationship("Tecnica", secondary=utensilio_tecnica_assoc)

class FeralInventario(Base):
    __tablename__ = 'feral_inventario'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    feral_id = Column(Integer, ForeignKey('feral.id', ondelete="CASCADE"), nullable=False)
    utensilio_id = Column(Integer, ForeignKey('utensilio.id', ondelete="RESTRICT"), nullable=False)
    durabilidade_atual = Column(Integer, nullable=False)
    se_quebrado = Column(Boolean, default=False)
    
    feral = relationship("Feral", back_populates="inventario")
    utensilio = relationship("Utensilio")
    tecnicas = relationship("Tecnica", secondary=feral_inventario_tecnica_assoc)