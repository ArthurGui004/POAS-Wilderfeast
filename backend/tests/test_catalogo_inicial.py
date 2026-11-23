import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from app.config import settings


class CatalogoInicialTest(unittest.TestCase):
    def test_migracao_preserva_inventario_e_cria_seis_opcoes(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta, "campanha.db")
            cfg = Config("alembic.ini")
            with patch.object(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{caminho.as_posix()}"):
                command.upgrade(cfg, "a2630edb941f")
                with closing(sqlite3.connect(caminho)) as db, db:
                    db.executescript("""
                        INSERT INTO usuario (id, nome, email, senha_hash) VALUES (1, 'Lia', 'lia@example.test', 'teste');
                        INSERT INTO feral (id, usuario_id, nome, vigor_max, vigor_atual) VALUES (1, 1, 'Lia', 10, 8);
                        INSERT INTO utensilio (id, nome, durabilidade_max, usuario_id) VALUES (91, 'Panela', 8, 1);
                        INSERT INTO utensilio (id, nome, durabilidade_max) VALUES (92, 'Cutelo de Ferro', 5);
                        INSERT INTO feral_inventario (id, feral_id, utensilio_id, durabilidade_atual)
                        VALUES (1, 1, 91, 2);
                    """)
                command.upgrade(cfg, "ba7234711ebe")
                with closing(sqlite3.connect(caminho)) as db, db:
                    db.executescript("""
                        INSERT INTO feral_inventario (id, feral_id, utensilio_id, durabilidade_atual, se_quebrado)
                        SELECT 2, 1, id, 16, 0 FROM utensilio WHERE nome = 'Panela' AND usuario_id IS NULL;
                        INSERT INTO feral_inventario (id, feral_id, utensilio_id, durabilidade_atual, se_quebrado)
                        SELECT 3, 1, id, 0, 1 FROM utensilio WHERE nome = 'Panela' AND usuario_id IS NULL;
                    """)
                command.upgrade(cfg, "head")
                command.upgrade(cfg, "head")
            with closing(sqlite3.connect(caminho)) as db:
                disponiveis = db.execute("""
                    SELECT nome, durabilidade_max FROM utensilio
                    WHERE disponivel_na_criacao AND usuario_id IS NULL ORDER BY nome
                """).fetchall()
                self.assertEqual(disponiveis, [(nome, 50 if nome == "Panela" else 20) for nome in
                                 ("Barbante", "Cutelo", "Espeto", "Luvas", "Maçarico", "Panela")])
                self.assertEqual(db.execute("""
                    SELECT u.alcance, t.nome FROM utensilio u
                    JOIN utensilio_tecnica ut ON ut.utensilio_id = u.id
                    JOIN tecnica t ON t.id = ut.tecnica_id WHERE u.nome = 'Maçarico'
                """).fetchone(), ("1 (Golpe), 3 (Tiro)", "Linha de Fogo"))
                self.assertEqual(db.execute("""
                    SELECT durabilidade_atual, se_quebrado FROM feral_inventario
                    WHERE id IN (2, 3) ORDER BY id
                """).fetchall(), [(46, 0), (0, 1)])
                antigos = db.execute("""
                    SELECT u.id, u.durabilidade_max, u.disponivel_na_criacao, i.durabilidade_atual
                    FROM feral_inventario i JOIN utensilio u ON u.id = i.utensilio_id WHERE i.id = 1
                """).fetchall()
                self.assertEqual(antigos, [(91, 8, 0, 2)])
                self.assertEqual(db.execute("""
                    SELECT nome, arquivado FROM utensilio
                    WHERE nome IN ('Cutelo', 'Cutelo de Ferro') ORDER BY nome
                """).fetchall(), [("Cutelo", 0), ("Cutelo de Ferro", 1)])
