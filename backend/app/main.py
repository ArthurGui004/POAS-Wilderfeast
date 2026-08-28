import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.config import settings
from app.seeds.seed_condicao import criar_condicoes_padrao
from app.routers import auth_router, feral_router, monstro_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await criar_condicoes_padrao()
    yield

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


@app.get("/")
async def root():
    return {"mensagem": "Wilderfeast API pronta para uso!"}
