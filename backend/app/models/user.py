from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Usuario(Base):
    __tablename__ = 'usuario'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    
    # Relação com Feral (A string "Feral" será resolvida pelo SQLAlchemy)
    ferais = relationship("Feral", back_populates="usuario", cascade="all, delete-orphan")
