from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Usuario
from app.schemas import UsuarioCreate
from app.security import hash_password

async def obter_usuario_por_email(db: AsyncSession, email: str) -> Usuario | None:
    query = select(Usuario).where(Usuario.email == email)
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()

async def criar_usuario(db: AsyncSession, usuario: UsuarioCreate) -> Usuario:
    novo_usuario = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=hash_password(usuario.senha)
    )
    db.add(novo_usuario)
    await db.commit()
    await db.refresh(novo_usuario)
    return novo_usuario