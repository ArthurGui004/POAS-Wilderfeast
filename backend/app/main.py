from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine
from app.preparar_banco import preparar_banco
from app.routers import auth_router, feral_router, monstro_router
from app.routers.equipamento import router as equipamento_router
from app.routers.imagens import router as imagens_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await preparar_banco()
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="Wilderfeast API",
    description="API do RPG Wilderfeast — Caçada e gerenciamento Feral",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins= settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(feral_router)
app.include_router(monstro_router)
app.include_router(equipamento_router)
app.include_router(imagens_router)


@app.get("/")
async def root():
    return {"mensagem": "Wilderfeast API pronta para uso!"}
