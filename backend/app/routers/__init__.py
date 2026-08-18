from .auth import router as auth_router
from .feral import router as feral_router
from .monstro import router as monstro_router

__all__ = ["auth_router", "feral_router", "monstro_router"]