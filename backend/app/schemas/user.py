from enum import Enum
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    nome: str[cite: 3]
    email: EmailStr[cite: 3]

class UserCreate(UserBase):
    senha: str[cite: 3]

class UserLogin(BaseModel):
    email: EmailStr[cite: 3]
    senha: str[cite: 3]

class UserOut(UserBase):
    id: int[cite: 3]
    model_config = ConfigDict(from_attributes=True)[cite: 3]

class Token(BaseModel):
    access_token: str[cite: 3]
    token_type: str = "bearer"[cite: 3]
    user: UserOut[cite: 3]