"""Preenche as URLs oficiais das ilustrações que ainda faltam no catálogo."""

import json
import re
from pathlib import Path

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Monstro, Utensilio
from app.seeds.seed_monstro import _normalizar


async def preencher_imagens_catalogo():
    imagens = json.loads(
        Path(__file__).with_name("imagens_catalogo.json").read_text(encoding="utf-8")
    )
    async with AsyncSessionLocal.begin() as db:
        monstros = await db.scalars(select(Monstro))
        utensilios = await db.scalars(select(Utensilio).where(
            Utensilio.usuario_id.is_(None),
            Utensilio.disponivel_na_criacao.is_(True),
            Utensilio.arquivado.is_(False),
        ))

        for registros, urls in ((monstros, imagens["monstros"]), (utensilios, imagens["utensilios"])):
            for registro in registros:
                chave = re.sub(r"[^a-z0-9]+", "-", _normalizar(registro.nome))
                if chave in urls and not (registro.imagem_url or "").strip():
                    registro.imagem_url = urls[chave]
