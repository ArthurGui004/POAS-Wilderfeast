from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.security import hash_password, verify_password, create_access_token
from app.models import Usuario
from app.schemas import UsuarioCreate, UsuarioResponse


router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(usuario: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    query = select(Usuario).where(Usuario.email == usuario.email)
    resultado = await db.execute(query)
    if resultado.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    
    novo_usuario = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=hash_password(usuario.senha)
    )
    db.add(novo_usuario)
    await db.commit()
    await db.refresh(novo_usuario)
    return novo_usuario

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    # O OAuth2PasswordRequestForm armazena o e-mail digitado no atributo 'username'
    query = select(Usuario).where(Usuario.email == form_data.username)
    resultado = await db.execute(query)
    usuario = resultado.scalar_one_or_none()
    
    # Valida se o usuário existe e se a senha está correta
    if not usuario or not verify_password(form_data.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Gera o token de acesso
    access_token = create_access_token(data={"sub": str(usuario.id)})
    
    return {"access_token": access_token, "token_type": "bearer", "usuario_id": usuario.id}

@router.post("/logout")
async def logout():
    return {"message": "Logout efetuado com sucesso."}