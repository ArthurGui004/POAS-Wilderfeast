import re
from urllib.parse import unquote, urlsplit

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.config import settings
from app.deps import get_current_user

router = APIRouter(tags=["Imagens"])
LIMITE = 4 * 1024 * 1024


class ImagemEnviada(BaseModel):
    url: str


def formato_imagem(dados: bytearray):
    if dados.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if dados.startswith(b"RIFF") and dados[8:12] == b"WEBP":
        return "webp"
    raise HTTPException(415, "Selecione uma imagem JPG, PNG ou WebP válida.")


def credenciais_cloudinary():
    config = settings.CLOUDINARY_URL
    try:
        url = urlsplit(config.get_secret_value() if config else "")
        if (url.scheme == "cloudinary" and url.username and url.password
                and re.fullmatch(r"[a-zA-Z0-9_-]+", url.hostname or "")):
            return url.hostname, (unquote(url.username), unquote(url.password))
    except ValueError:
        pass
    raise HTTPException(503, "O armazenamento de imagens na nuvem ainda não foi configurado.")


@router.post("/imagens/feral", response_model=ImagemEnviada, status_code=201,
             dependencies=[Depends(get_current_user)])
async def enviar_imagem(request: Request):
    nome_nuvem, credenciais = credenciais_cloudinary()
    dados = bytearray()
    async for pedaco in request.stream():
        if len(dados) + len(pedaco) > LIMITE:
            raise HTTPException(413, "A imagem deve ter no máximo 4 MB.")
        dados.extend(pedaco)
    formato = formato_imagem(dados)

    try:
        async with httpx.AsyncClient(timeout=20, trust_env=False) as cliente:
            resposta = await cliente.post(
                f"https://api.cloudinary.com/v1_1/{nome_nuvem}/image/upload",
                auth=credenciais,
                files={"file": (f"feral.{formato}", bytes(dados), f"image/{formato}")},
                data={"allowed_formats": "jpg,jpeg,png,webp", "folder": "wilderfeast/ferais"},
            )
            resposta.raise_for_status()
            url = resposta.json()["secure_url"]
            if not isinstance(url, str) or not url.startswith("https://"):
                raise ValueError("URL de imagem ausente ou inválida")
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        raise HTTPException(502, "Não foi possível enviar a imagem à nuvem. Tente novamente.") from None
    return ImagemEnviada(url=url)
