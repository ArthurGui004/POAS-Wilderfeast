from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, Table, select, false
from sqlalchemy.orm import relationship
from app.database import Base


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
    usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=True)
    # Marca os seis registros da migração original, inclusive para sua reversão.
    disponivel_na_criacao = Column(Boolean, nullable=False, server_default=false())
    arquivado = Column(Boolean, nullable=False, server_default=false())
    nome = Column(String(100), nullable=False)
    alcance = Column(String(50))
    durabilidade_max = Column(Integer, nullable=False)
    estilos_principais = Column(JSON, nullable=True)
    imagem_url = Column(Text)
    
    tecnicas = relationship("Tecnica", secondary=utensilio_tecnica_assoc)


def catalogo_disponivel(usuario_id: int | None):
    visivel = Utensilio.usuario_id.is_(None)
    if usuario_id is not None:
        visivel = visivel | (Utensilio.usuario_id == usuario_id)
    return select(Utensilio).where(visivel, Utensilio.arquivado.is_(False))


class FeralInventario(Base):
    __tablename__ = 'feral_inventario'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    feral_id = Column(Integer, ForeignKey('feral.id', ondelete="CASCADE"), nullable=False)
    utensilio_id = Column(Integer, ForeignKey('utensilio.id', ondelete="RESTRICT"), nullable=False)
    durabilidade_atual = Column(Integer, nullable=False)
    estilo_escolhido = Column(String(100))
    se_quebrado = Column(Boolean, default=False)
    
    feral = relationship("Feral", back_populates="inventario")
    utensilio = relationship("Utensilio")
    tecnicas = relationship("Tecnica", secondary=feral_inventario_tecnica_assoc)
