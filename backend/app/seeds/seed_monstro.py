"""
Insere/atualiza monstros no banco a partir dos JSONs de './seeds' (async).

As tabelas devem existir antes (alembic upgrade head) e os catálogos
(Estilo, Habilidade, Traco, Tecnica) devem estar populados.
"""

import asyncio
import json
import sys
import unicodedata
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal, engine
from app.enums import CategoriaMonstro
from app.models import (
    Monstro,
    MonstroEstilo,
    MonstroHabilidade,
    MonstroParte,
    Estilo,
    Habilidade,
    Traco,
    Tecnica,
)

DIR_SEEDS_PADRAO = Path("app/seeds/extract_monstro/seeds")


# ==========================================
# Helpers
# ==========================================
def _to_int(valor, padrao: int = 0) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return padrao


def _normalizar(texto: str) -> str:
    """minúsculas, sem acento e sem espaços nas pontas."""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return sem_acento.strip().lower()


def _parse_categoria(valor) -> CategoriaMonstro:
    """Aceita o nome OU o valor do enum, sem diferenciar maiúsculas/acentos."""
    membros = list(CategoriaMonstro)
    if valor:
        alvo = _normalizar(valor)
        for m in membros:
            if alvo in (_normalizar(m.name), _normalizar(m.value)):
                return m
        print(f"  [AVISO] Categoria '{valor}' inválida — usando '{membros[0].name}'.")
    return membros[0]


async def _buscar_por_nome(db: AsyncSession, modelo, nome: str):
    """Primeiro registro cujo nome bate, ignorando maiúsculas/minúsculas.

    Usa lower() == lower() em vez de ILIKE para que '%' e '_' no nome
    não sejam tratados como curingas.
    """
    resultado = await db.execute(
        select(modelo).where(func.lower(modelo.nome) == str(nome).strip().lower()).limit(1)
    )
    return resultado.scalars().first()


def _lista(valor) -> list:
    return valor if isinstance(valor, list) else []


def _texto_lista(valor) -> Optional[str]:
    if isinstance(valor, list):
        return ", ".join(str(v) for v in valor if v)
    return valor


# ==========================================
# Seed de um monstro
# ==========================================
async def seed_monstro(db: AsyncSession, dados: dict) -> None:
    if not isinstance(dados, dict):
        raise ValueError("O JSON do monstro deve ser um objeto.")

    nome_monstro = dados.get("nome")
    if not nome_monstro:
        raise ValueError("O JSON fornecido não contém o campo 'nome'.")

    # Sem lazy loading no async: carrega antes as coleções que serão alteradas.
    resultado = await db.execute(
        select(Monstro)
        .where(Monstro.nome == nome_monstro)
        .options(
            selectinload(Monstro.estilos),
            selectinload(Monstro.habilidades),
            selectinload(Monstro.tracos),
            selectinload(Monstro.partes),
        )
    )
    monstro = resultado.scalars().first()

    if monstro is None:
        monstro = Monstro(
            nome=nome_monstro,
            estilos=[],
            habilidades=[],
            tracos=[],
            partes=[],
        )
        db.add(monstro)

    # Atributos básicos
    monstro.categoria = _parse_categoria(dados.get("categoria"))
    monstro.vigor_base = _to_int(dados.get("vigor_base") or 30, 30)
    monstro.vigor_atual = _to_int(dados.get("vigor_atual") or monstro.vigor_base, monstro.vigor_base)
    monstro.historia = dados.get("historia")
    monstro.comportamento = dados.get("comportamento")
    monstro.dieta = _texto_lista(dados.get("dieta"))
    monstro.habitat = _texto_lista(dados.get("habitat"))

    # Limpa as coleções filhas e EXECUTA os deletes agora. Sem esse flush, o
    # SQLAlchemy faz INSERT antes de DELETE na mesma transação e, ao reprocessar
    # um monstro, recriar a mesma linha pode violar chaves únicas.
    monstro.estilos.clear()
    monstro.habilidades.clear()
    monstro.partes.clear()
    await db.flush()

    # Estilos
    estilos_dados = dados.get("estilos") or {}
    vistos = set()
    if isinstance(estilos_dados, dict):
        for nome_estilo, pontos in estilos_dados.items():
            if pontos is None:
                continue
            estilo_obj = await _buscar_por_nome(db, Estilo, nome_estilo)
            if not estilo_obj:
                print(f"  [AVISO] Estilo '{nome_estilo}' não encontrado no banco — pulando.")
                continue
            if estilo_obj.id in vistos:
                continue
            vistos.add(estilo_obj.id)
            monstro.estilos.append(MonstroEstilo(estilo=estilo_obj, pontos=_to_int(pontos)))

    # Habilidades
    vistos = set()
    for hab_item in _lista(dados.get("habilidades")):
        if isinstance(hab_item, dict):
            nome_hab = hab_item.get("nome")
            pontos_hab = _to_int(hab_item.get("valor"), 0)
        else:
            nome_hab = str(hab_item) if hab_item else None
            pontos_hab = 0
        if not nome_hab:
            continue

        hab_obj = await _buscar_por_nome(db, Habilidade, nome_hab)
        if not hab_obj:
            print(f"  [AVISO] Habilidade '{nome_hab}' não encontrada no banco — pulando.")
            continue
        if hab_obj.id in vistos:
            continue
        vistos.add(hab_obj.id)
        monstro.habilidades.append(MonstroHabilidade(habilidade=hab_obj, pontos=pontos_hab))

    # Traços (N:N)
    nomes_tracos = []
    for t in _lista(dados.get("tracos")):
        if isinstance(t, dict) and t.get("nome"):
            nomes_tracos.append(t["nome"])
        elif isinstance(t, str) and t:
            nomes_tracos.append(t)
    for t_adj in _lista(dados.get("tracos_adicionais")):
        if isinstance(t_adj, str) and t_adj:
            nomes_tracos.append(t_adj)

    novos_tracos = []
    for nome_t in nomes_tracos:
        traco_obj = await _buscar_por_nome(db, Traco, nome_t)
        if not traco_obj:
            print(f"  [AVISO] Traço '{nome_t}' não encontrado no banco — pulando.")
        elif traco_obj not in novos_tracos:
            novos_tracos.append(traco_obj)
    monstro.tracos = novos_tracos

    # Partes
    for parte_data in _lista(dados.get("partes")):
        if not isinstance(parte_data, dict):
            continue
        nome_parte = parte_data.get("nome")
        if not nome_parte:
            continue

        dur_max = _to_int(parte_data.get("durabilidade") or 30, 30)
        dur_atual_raw = parte_data.get("durabilidade_atual")
        dur_atual = _to_int(dur_atual_raw, dur_max) if dur_atual_raw is not None else dur_max
        alcance = parte_data.get("alcance")

        nome_tecnica = parte_data.get("tecnica") or nome_parte
        tecnica_obj = await _buscar_por_nome(db, Tecnica, nome_tecnica)
        if not tecnica_obj:
            resultado_tec = await db.execute(select(Tecnica).order_by(Tecnica.id).limit(1))
            tecnica_obj = resultado_tec.scalars().first()
            if tecnica_obj:
                print(
                    f"  [AVISO] Técnica '{nome_tecnica}' não encontrada — usando "
                    f"'{tecnica_obj.nome}' na parte '{nome_parte}'."
                )

        if not tecnica_obj:
            print(
                f"  [AVISO] Nenhuma Técnica cadastrada no banco para associar "
                f"à parte '{nome_parte}' — pulando parte."
            )
            continue

        monstro.partes.append(
            MonstroParte(
                nome=nome_parte,
                tecnica=tecnica_obj,
                alcance=str(alcance) if alcance is not None else None,
                durabilidade_max=dur_max,
                durabilidade_atual=dur_atual,
                se_quebrado=bool(parte_data.get("se_quebrado")),
            )
        )

    # Lê id/nome antes do commit (evita refresh pós-commit, que falha no async).
    await db.flush()
    monstro_id = monstro.id
    monstro_nome = monstro.nome
    await db.commit()
    print(f"  ✅ Salvo no banco: Monstro '{monstro_nome}' (id={monstro_id}).")


# ==========================================
# Fluxo principal
# ==========================================
async def criar_monstros_padrao(dir_seeds: Optional[Path] = None) -> int:
    """Retorna o número de erros ocorridos (0 = tudo certo)."""
    dir_seeds = dir_seeds or DIR_SEEDS_PADRAO

    if not dir_seeds.exists():
        print(f"❌ O diretório '{dir_seeds}' não existe.")
        return 1

    if dir_seeds.is_file() and dir_seeds.suffix == ".json":
        arquivos_json = [dir_seeds]
    else:
        arquivos_json = sorted(dir_seeds.glob("*.json"))

    if not arquivos_json:
        print(f"Nenhum arquivo .json encontrado na pasta '{dir_seeds}'.")
        return 0

    print(f"🌱 Encontrados {len(arquivos_json)} arquivo(s) JSON de monstros...\n")

    sucesso_count = 0
    erro_count = 0

    for arquivo_path in arquivos_json:
        print(f"📄 Processando seed: {arquivo_path.name}...")
        try:
            dados = json.loads(arquivo_path.read_text(encoding="utf-8"))
            # Uma sessão por arquivo: se falhar, o rollback é automático ao fechar.
            async with AsyncSessionLocal() as db:
                await seed_monstro(db, dados)
            sucesso_count += 1
        except Exception as e:
            erro_count += 1
            print(f"  ❌ Erro ao processar '{arquivo_path.name}': {e}")
        print("-" * 50)

    print(f"\n✨ Monstros finalizados! Sucessos: {sucesso_count} | Erros: {erro_count}")
    return erro_count


async def _main(dir_seeds: Optional[Path]) -> None:
    try:
        await criar_monstros_padrao(dir_seeds)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main(Path(sys.argv[1]) if len(sys.argv) > 1 else None))