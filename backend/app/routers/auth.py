from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.security import verify_password, create_access_token
from app.schemas import UsuarioCreate, UsuarioResponse
from app.crud import crud_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(usuario: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    if await crud_user.obter_usuario_por_email(db, usuario.email):
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    return await crud_user.criar_usuario(db, usuario)


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    usuario = await crud_user.obter_usuario_por_email(db, form_data.username)
    if not usuario or not verify_password(form_data.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(usuario.id)})
    return {"access_token": access_token, "token_type": "bearer", "usuario_id": usuario.id}


@router.post("/logout")
async def logout():
    return {"message": "Logout efetuado com sucesso."}