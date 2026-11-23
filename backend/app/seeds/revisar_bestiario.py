"""Concilia o Bestiário com os dados estruturados conferidos no Livro Básico."""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal, engine
from app.enums import CategoriaMonstro
from app.models import Estilo, Habilidade, Monstro, MonstroEstilo, MonstroHabilidade, MonstroParte, Tecnica, Traco
from app.seeds.seed_monstro import _normalizar


async def revisar_bestiario():
    fichas = json.loads(Path(__file__).with_name("bestiario_revisado.json").read_text(encoding="utf-8"))
    async with AsyncSessionLocal.begin() as db:
        consulta = select(Monstro).options(
            selectinload(Monstro.estilos),
            selectinload(Monstro.habilidades),
            selectinload(Monstro.tracos),
            selectinload(Monstro.partes),
        )
        monstros = {_normalizar(m.nome): m for m in (await db.scalars(consulta)).all()}
        estilos = {e.nome.upper(): e for e in (await db.scalars(select(Estilo))).all()}
        habilidades = {h.nome.upper(): h for h in (await db.scalars(select(Habilidade))).all()}
        tracos = {_normalizar(t.nome): t for t in (await db.scalars(select(Traco))).all()}

        for ficha in fichas:
            nome = ficha["nome"]
            monstro = monstros.get(_normalizar(nome)) or monstros.get(_normalizar(ficha.get("alias", nome)))
            if monstro is None:
                monstro = Monstro(
                    nome=nome, categoria=CategoriaMonstro.Adulto, vigor_base=30, vigor_atual=30,
                    estilos=[], habilidades=[], tracos=[], partes=[],
                )
                db.add(monstro)

            if not (monstro.historia or "").strip():
                linhagem = ficha.get("linhagem")
                edicao = ficha.get("edicao", "edição em português")
                referencia = f"Ficha de referência no Livro Básico de Wilderfeast ({edicao}, p. {ficha['pagina']})."
                monstro.historia = f"Linhagem dos {linhagem}. {referencia}" if linhagem else referencia
            for campo in ("habitat", "dieta", "comportamento"):
                if ficha.get(campo) and not (getattr(monstro, campo) or "").strip():
                    setattr(monstro, campo, ficha[campo])

            atualizar_pontos(monstro.estilos, ficha["estilos"], estilos, MonstroEstilo, "estilo")
            atualizar_pontos(monstro.habilidades, ficha["habilidades"], habilidades, MonstroHabilidade, "habilidade")

            associados = {_normalizar(t.nome) for t in monstro.tracos}
            for nome_traco in ficha["tracos"]:
                chave = _normalizar(nome_traco)
                if chave not in tracos:
                    tracos[chave] = Traco(nome=nome_traco)
                    db.add(tracos[chave])
                if chave not in associados:
                    monstro.tracos.append(tracos[chave])
                    associados.add(chave)

            partes = {_normalizar(p.nome): p for p in monstro.partes}
            for dados in ficha["partes"]:
                maximo = dados["durabilidade"]
                parte = partes.get(_normalizar(dados["nome"]))
                if parte is None:
                    parte = MonstroParte(
                        nome=dados["nome"], durabilidade_max=maximo, durabilidade_atual=maximo,
                        tecnica=Tecnica(nome=dados["nome"]),
                    )
                    monstro.partes.append(parte)
                elif parte.durabilidade_max != maximo:
                    # Conserva o dano acumulado. Uma parte quebrada permanece em zero.
                    if parte.durabilidade_atual > 0:
                        dano = max(0, parte.durabilidade_max - parte.durabilidade_atual)
                        parte.durabilidade_atual = max(0, maximo - dano)
                    parte.durabilidade_max = maximo
                if dados.get("alcance") and not (parte.alcance or "").strip():
                    parte.alcance = dados["alcance"]

    print(f"Bestiário revisado: {len(fichas)} fichas do Livro Básico.")


def atualizar_pontos(associacoes, valores, catalogo, modelo, chave):
    vinculados = {getattr(item, f"{chave}_id"): item for item in associacoes}
    for nome, pontos in valores.items():
        atributo = catalogo[nome]
        item = vinculados.get(atributo.id)
        if item is None:
            associacoes.append(modelo(**{chave: atributo}, pontos=pontos))
        else:
            item.pontos = pontos


async def main():
    try:
        await revisar_bestiario()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
