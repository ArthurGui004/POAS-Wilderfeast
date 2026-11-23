import base64
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import settings
from app.deps import get_current_user
from app.main import app
from app.routers.imagens import LIMITE

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jH1sAAAAASUVORK5CYII="
)
CONFIG = SecretStr("cloudinary://chave:segredo@nuvem-teste")
ROTA = "/imagens/feral"


class ImagensTest(unittest.TestCase):
    def setUp(self):
        self.http = TestClient(app)
        self.addCleanup(self.http.close)
        self.addCleanup(app.dependency_overrides.pop, get_current_user, None)

    def test_exige_sessao_e_configuracao(self):
        self.assertEqual(self.http.post(ROTA, content=PNG).status_code, 401)
        app.dependency_overrides[get_current_user] = lambda: object()
        with patch.object(settings, "CLOUDINARY_URL", None):
            self.assertEqual(self.http.post(ROTA, content=PNG).status_code, 503)

    def test_conteudo_invalido_e_limite(self):
        app.dependency_overrides[get_current_user] = lambda: object()
        with patch.object(settings, "CLOUDINARY_URL", CONFIG):
            self.assertEqual(self.http.post(ROTA, content=b"<svg/>").status_code, 415)
            self.assertEqual(self.http.post(ROTA, content=b"x" * (LIMITE + 1)).status_code, 413)

    def test_envia_o_arquivo_ao_cloudinary_e_devolve_url_https(self):
        app.dependency_overrides[get_current_user] = lambda: object()
        url = "https://res.cloudinary.com/nuvem-teste/image/upload/feral.png"

        async def receber(pedido):
            self.assertEqual(str(pedido.url), "https://api.cloudinary.com/v1_1/nuvem-teste/image/upload")
            self.assertTrue(pedido.headers["Authorization"].startswith("Basic "))
            self.assertIn(PNG, await pedido.aread())
            return httpx.Response(201, json={"secure_url": url})

        transporte = httpx.MockTransport(receber)
        cliente = httpx.AsyncClient(transport=transporte)
        with patch.object(settings, "CLOUDINARY_URL", CONFIG), patch(
            "app.routers.imagens.httpx.AsyncClient", return_value=cliente
        ):
            resposta = self.http.post(ROTA, content=PNG)
        self.assertEqual(resposta.status_code, 201, resposta.text)
        self.assertEqual(resposta.json(), {"url": url})
