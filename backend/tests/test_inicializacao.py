import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class InicializacaoTest(unittest.TestCase):
    def test_api_prepara_banco_vazio_e_preserva_registros_ao_reiniciar(self):
        with tempfile.TemporaryDirectory() as pasta:
            banco = Path(pasta, "deploy.db")
            env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{banco.as_posix()}"}
            resultado = subprocess.run(
                [sys.executable, "-c", """
import sqlite3
import sys
from contextlib import closing
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as api:
    monstros = api.get("/monstro/").json()
    utensilios = api.get("/utensilio/").json()
    assert len(monstros) == 40, monstros
    assert {u["nome"] for u in utensilios} == {
        "Barbante", "Cutelo", "Espeto", "Luvas", "Maçarico", "Panela"
    }, utensilios
    assert all((r["imagem_url"] or "").startswith("https://res.cloudinary.com/")
               for r in monstros + utensilios)
    chamig = next(m for m in monstros if m["nome"] == "CHAMIG")
    ficha = api.get(f"/monstro/{chamig['id']}").json()
    assert ficha["partes"] and ficha["tracos"] and ficha["estilos"]
    assert ficha["imagem_url"] == chamig["imagem_url"]

parte = ficha["partes"][0]["id"]
panela = next(u for u in utensilios if u["nome"] == "Panela")
personalizada = "https://example.test/chamig.jpg"
with closing(sqlite3.connect(sys.argv[1])) as db, db:
    assert db.execute("SELECT count(imagem_url) FROM monstro").fetchone() == (40,)
    assert db.execute("SELECT count(imagem_url) FROM utensilio").fetchone() == (6,)
    db.execute("UPDATE monstro SET vigor_atual = 19, imagem_url = ? WHERE id = ?",
               (personalizada, chamig["id"]))
    db.execute("UPDATE monstro_parte SET durabilidade_atual = 2 WHERE id = ?", (parte,))
    db.execute("UPDATE utensilio SET imagem_url = NULL WHERE id = ?", (panela["id"],))
    db.execute("INSERT INTO utensilio (nome, durabilidade_max) VALUES ('Concha', 12)")

with TestClient(app) as api:
    assert len(api.get("/monstro/").json()) == 40
    utensilios = {u["nome"]: u for u in api.get("/utensilio/").json()}
    assert len(utensilios) == 7
    assert utensilios["Panela"]["imagem_url"] == panela["imagem_url"]
    assert utensilios["Concha"]["imagem_url"] is None
    ficha = api.get(f"/monstro/{chamig['id']}").json()
    assert ficha["vigor_atual"] == 19, ficha
    assert ficha["imagem_url"] == personalizada
    assert next(p for p in ficha["partes"] if p["id"] == parte)["durabilidade_atual"] == 2
""", str(banco)],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
