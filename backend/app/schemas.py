from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str

class UserLogin(BaseModel):
    email: EmailStr
    senha: str

class UserResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    criado_em: datetime

    class Config:
        from_attributes = True