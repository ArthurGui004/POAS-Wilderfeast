from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from app.security import hash_password, verify_password, create_access_token
from backend.app.functions import get_current_user

router = APIRouter(prefix="/auth", tags=["autenticação"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existente = (await db.execute(select(User).filter_by(email=payload.email))).scalar()
    if existente:
        raise HTTPException(status_code=403, detail="ERRO 403! Este usuário já existe.")

    user = User(nome=payload.nome, email=payload.email, senha_hash=hash_password(payload.senha))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).filter_by(email=payload.email))).scalar()
    if not user:
        raise HTTPException(status_code=404, detail="ERRO 404! Usuário não cadastrado")
    if not verify_password(payload.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="ERRO 401! Verifique sua senha e tente novamente")

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/usuarios/count", response_model=int)
async def contar_jogadores(db: AsyncSession = Depends(get_db)):
    """Retorna o número total de usuários cadastrados no banco."""
    result = await db.execute(select(func.count(User.id)))
    total = result.scalar()
    return total or 0
