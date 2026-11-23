"""Testes HTTP com JWT real e banco descartável."""
import asyncio
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import Estilo, Tecnica, Utensilio
from app.models.condicao import Condicao


class FichasTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        caminho = Path(self.pasta.name, "jogo.db").as_posix()
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{caminho}")
        self.sessoes = async_sessionmaker(self.engine, expire_on_commit=False)

        async def banco():
            async with self.sessoes() as db:
                yield db

        async def preparar():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            async with self.sessoes() as db:
                db.add_all([Estilo(nome="Preciso"), Condicao(nome="Exposto"),
                            Utensilio(nome="Cutelo", durabilidade_max=5, disponivel_na_criacao=True,
                                      estilos_principais=["Poderoso", "Preciso"],
                                      tecnicas=[Tecnica(nome="Corte")]),
                            Utensilio(nome="Espeto", durabilidade_max=20, disponivel_na_criacao=True),
                            Utensilio(nome="Cutelo antigo", durabilidade_max=5),
                            Utensilio(id=90, nome="Cutelo de Ferro", durabilidade_max=5, arquivado=True)])
                await db.commit()

        asyncio.run(preparar())
        app.dependency_overrides[get_db] = banco
        self.http = TestClient(app)
        self.dono = self.entrar("lia")
        self.outro = self.entrar("rui")
        self.feral = self.criar_ficha(self.dono)
        self.url = f"/feral/{self.feral}"

    def tearDown(self):
        self.http.close()
        app.dependency_overrides.pop(get_db)
        asyncio.run(self.engine.dispose())
        self.pasta.cleanup()

    def entrar(self, nome):
        email = f"{nome}@example.com"
        resposta = self.http.post("/auth/registro", json={"email": email, "nome": nome, "senha": "senha-de-teste"})
        self.assertEqual(resposta.status_code, 201, resposta.text)
        login = self.http.post("/auth/login", data={"username": email, "password": "senha-de-teste"})
        return {"Authorization": "Bearer " + login.json()["access_token"]}

    def criar_ficha(self, dono, utensilio_id=1):
        r = self.http.post("/feral/", headers=dono, json={"nome": "Feral", "vigor_max": 8, "vigor_atual": 8, "utensilio_id": utensilio_id})
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["id"]

    def test_inventario(self):
        url = self.url + "/inventario"
        http = self.http
        catalogo = http.get("/utensilio/").json()
        self.assertEqual(catalogo[0]["tecnicas"][0]["nome"], "Corte")
        self.assertEqual(http.get(url).status_code, 401)
        itens = http.get(url, headers=self.dono).json()
        self.assertEqual(len(itens), 1)
        item = itens[0]
        self.assertEqual(item["utensilio"]["id"], catalogo[0]["id"])
        self.assertEqual(item["durabilidade_atual"], 5)
        self.assertIsNone(item["estilo_escolhido"])
        endereco = f"{url}/{item['id']}"
        self.assertEqual(http.get(url, headers=self.outro).status_code, 404)
        self.assertEqual(http.put(endereco, headers=self.outro, json={"durabilidade_atual": 1}).status_code, 404)
        outra_ficha = self.criar_ficha(self.dono)
        self.assertEqual(http.put(f"/feral/{outra_ficha}/inventario/{item['id']}", headers=self.dono, json={"durabilidade_atual": 1}).status_code, 404)
        estilo = f"{endereco}/estilo"
        for dono, nome, status in [
            (self.outro, "Preciso", 404),
            (self.dono, "Ligeiro", 422),
            (self.dono, "Preciso", 200),
            (self.dono, "Poderoso", 200),
        ]:
            self.assertEqual(http.put(estilo, headers=dono, json={"estilo_escolhido": nome}).status_code, status)
        for valor in (-1, 6):
            self.assertEqual(http.put(endereco, headers=self.dono, json={"durabilidade_atual": valor}).status_code, 422)
        for valor in (0, 3):
            dado = {"durabilidade_atual": valor}
            self.assertEqual(http.put(endereco, headers=self.dono, json=dado).status_code, 200)
            salvo = http.get(url, headers=self.dono).json()[0]
            self.assertEqual(salvo["durabilidade_atual"], valor)
            self.assertEqual(salvo["se_quebrado"], valor == 0)
            self.assertEqual(salvo["estilo_escolhido"], "Poderoso")
        self.assertEqual(http.get(f"/feral/{outra_ficha}/inventario", headers=self.dono).json()[0]["durabilidade_atual"], 5)
        self.assertEqual(http.delete(endereco, headers=self.dono).status_code, 405)
        self.assertEqual(http.post(url, headers=self.dono, json={"utensilio_id": 2}).status_code, 405)

    def test_itens_encontrados(self):
        url = self.url + "/itens-encontrados"
        http = self.http
        dados = {"nome": "  Fruto silvestre ", "quantidade": 3, "descricao": " Fresco "}
        self.assertEqual(http.get(url).status_code, 401)
        self.assertEqual(http.get(url, headers=self.outro).status_code, 404)
        self.assertEqual(http.post(url, headers=self.outro, json=dados).status_code, 404)
        for invalido in ({"nome": " "}, {"quantidade": 0}, {"quantidade": 1.5}):
            self.assertEqual(http.post(url, headers=self.dono, json={**dados, **invalido}).status_code, 422)
        novo = http.post(url, headers=self.dono, json=dados)
        self.assertEqual(novo.status_code, 201, novo.text)
        self.assertEqual(novo.json(), {
            "id": novo.json()["id"], "nome": "Fruto silvestre", "quantidade": 3, "descricao": "Fresco",
        })
        self.assertEqual(http.get(url, headers=self.dono).json(), [novo.json()])
        outra_ficha = self.criar_ficha(self.dono)
        self.assertEqual(http.get(f"/feral/{outra_ficha}/itens-encontrados", headers=self.dono).json(), [])
        self.assertEqual(len(http.get(self.url + "/inventario", headers=self.dono).json()), 1)
        endereco = f"{url}/{novo.json()['id']}"
        alterado = {"nome": "Fruto seco", "quantidade": 1, "descricao": ""}
        self.assertEqual(http.put(endereco, headers=self.outro, json=alterado).status_code, 404)
        outro_endereco = f"/feral/{outra_ficha}/itens-encontrados/{novo.json()['id']}"
        self.assertEqual(http.patch(outro_endereco, headers=self.dono, json={"variacao": 1}).status_code, 404)
        for variacao, esperado in [(1, 4), (-1, 3)]:
            r = http.patch(endereco, headers=self.dono, json={"variacao": variacao})
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.json()["quantidade"], esperado)
            self.assertEqual(r.json()["nome"], "Fruto silvestre")
        r = http.put(endereco, headers=self.dono, json=alterado)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json(), {**alterado, "id": novo.json()["id"], "descricao": None})
        self.assertEqual(http.get(url, headers=self.dono).json(), [r.json()])
        self.assertEqual(http.patch(endereco, headers=self.dono, json={"variacao": -1}).status_code, 204)
        self.assertEqual(http.get(url, headers=self.dono).json(), [])
        self.assertEqual(http.patch(endereco, headers=self.dono, json={"variacao": -1}).status_code, 404)

        outro = http.post(url, headers=self.dono, json=dados).json()
        endereco = f"{url}/{outro['id']}"
        self.assertEqual(http.put(endereco, headers=self.outro, json={**alterado, "quantidade": 0}).status_code, 404)
        self.assertEqual(http.put(endereco, headers=self.dono, json={**alterado, "quantidade": 0}).status_code, 204)
        self.assertEqual(http.get(url, headers=self.dono).json(), [])

    def test_atributos(self):
        url = self.url + "/atributos"
        for grupo, valor in [("condicoes", 1), ("estilos", 3)]:
            dados = {"grupo": grupo, "valor": valor, "id": 1}
            self.assertEqual(self.http.put(url, headers=self.outro, json=dados).status_code, 404)
            for _ in range(2):
                self.assertEqual(self.http.put(url, headers=self.dono, json=dados).status_code, 200)
            self.assertEqual(self.http.get(url, headers=self.dono).json()[grupo][0]["valor"], valor)
            self.assertEqual(self.http.put(url, headers=self.dono, json={**dados, "valor": 0}).status_code, 200)
            self.assertEqual(self.http.get(url, headers=self.dono).json()[grupo][0]["valor"], 0)
        for grupo, id_, valor, status in [("condicoes", 1, 2, 422), ("estilos", 99, 1, 404)]:
            r = self.http.put(url, headers=self.dono, json={"grupo": grupo, "id": id_, "valor": valor})
            self.assertEqual(r.status_code, status)

    def test_selecao_inicial(self):
        catalogo = self.http.get("/utensilio/").json()
        self.assertEqual([u["nome"] for u in catalogo], ["Cutelo", "Cutelo antigo", "Espeto"])
        self.assertEqual(self.http.post("/utensilio/", headers=self.dono, json={"nome": "Outro"}).status_code, 405)
        payload = {"nome": "Lia", "vigor_atual": 8, "vigor_max": 8}
        for escolha in ({}, {"utensilio_id": 999}, {"utensilio_id": 0}, {"utensilio_id": 90}):
            r = self.http.post("/feral/", headers=self.dono, json={**payload, **escolha})
            self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(len(self.http.get("/feral/meus", headers=self.dono).json()), 1)
        ficha = self.criar_ficha(self.dono, 2)
        self.assertEqual(self.http.put(f"/feral/{ficha}", headers=self.dono, json=payload).status_code, 200)
        itens = self.http.get(f"/feral/{ficha}/inventario", headers=self.dono).json()
        self.assertEqual([(i["utensilio"]["nome"], i["durabilidade_atual"]) for i in itens], [("Espeto", 20)])
        detalhe = self.http.get(f"/feral/{ficha}", headers=self.dono).json()
        self.assertEqual(detalhe["inventario"], [{"id": itens[0]["id"], "nome": "Espeto"}])

    def test_novo_utensilio_do_banco_disponivel_sem_ficha(self):
        with closing(sqlite3.connect(Path(self.pasta.name, "jogo.db"))) as db, db:
            novo = db.execute("INSERT INTO utensilio (nome, durabilidade_max) VALUES ('Concha', 14)").lastrowid
            pessoal = db.execute("""
                INSERT INTO utensilio (nome, durabilidade_max, usuario_id)
                SELECT 'Colher da Lia', 9, id FROM usuario WHERE email = 'lia@example.com'
            """).lastrowid
        self.assertEqual(self.http.get("/feral/meus", headers=self.outro).json(), [])
        for sessao in ({}, self.outro, self.dono):
            resposta = self.http.get("/utensilio/", headers=sessao)
            ids = [u["id"] for u in resposta.json()]
            self.assertIn(novo, ids)
            self.assertEqual(pessoal in ids, sessao == self.dono)
        payload = {"nome": "Rui", "vigor_max": 8, "vigor_atual": 8, "utensilio_id": pessoal}
        self.assertEqual(self.http.post("/feral/", headers=self.outro, json=payload).status_code, 422)
        for sessao, escolha, durabilidade in ((self.outro, novo, 14), (self.dono, pessoal, 9)):
            ficha = self.criar_ficha(sessao, escolha)
            [item] = self.http.get(f"/feral/{ficha}/inventario", headers=sessao).json()
            self.assertEqual((item["utensilio"]["id"], item["durabilidade_atual"]), (escolha, durabilidade))
