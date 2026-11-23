"""Prepara o esquema e preenche o catálogo antes de a API receber tráfego."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.database import engine
from app.seeds.revisar_bestiario import revisar_bestiario
from app.seeds.seed_condicao import criar_condicoes_padrao
from app.seeds.seed_estilo import criar_estilos_padrao
from app.seeds.seed_habilidade import criar_habilidades_padrao
from app.seeds.seed_imagens_catalogo import preencher_imagens_catalogo
from app.seeds.seed_monstro import criar_monstros_padrao
from app.seeds.seed_tracos import pipeline_criar_tracos


def aplicar_migracoes(conexao):
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["connection"] = conexao
    command.upgrade(config, "head")


async def preparar_banco():
    # O bloqueio dura até o fim da carga, inclusive entre instâncias do deploy.
    async with engine.begin() as bloqueio:
        if engine.dialect.name == "postgresql":
            await bloqueio.execute(text("SELECT pg_advisory_xact_lock(33047258031)"))
        async with engine.connect() as conexao:
            await conexao.run_sync(aplicar_migracoes)
            await conexao.commit()

        await criar_estilos_padrao()
        await criar_habilidades_padrao()
        await criar_condicoes_padrao()
        if await pipeline_criar_tracos(preencher_apenas=True):
            raise RuntimeError("O catálogo de traços está vazio.")
        if await criar_monstros_padrao(somente_novos=True):
            raise RuntimeError("A carga inicial dos monstros falhou.")
        await revisar_bestiario()
        await preencher_imagens_catalogo()
