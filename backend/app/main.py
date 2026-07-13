from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.database import init_db
from app.seed import criar_condicoes_padrao
from app.config import settings
from app.routers import auth, feral, bestiario


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await criar_condicoes_padrao()
    yield


app = FastAPI(
    title="Wilderfeast API",
    description="API do RPG Wilderfeast — sistema Feral (personagens) e Bestiário",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(feral.router)
app.include_router(bestiario.router)


@app.get("/")
async def root():
    return {"mensagem": "Wilderfeast API — a Caçada começa aqui."}
