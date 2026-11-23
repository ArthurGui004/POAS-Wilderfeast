"""Aplica as regras iniciais do Livro Básico, pp. 13–19, aos seis modelos oficiais."""

import sqlalchemy as sa
from alembic import op

revision = "d1c641bf980e"
down_revision = "ba7234711ebe"
branch_labels = None
depends_on = None

GOLPE = "1 (Golpe)"
MODELOS = {
    "Barbante": (["Ligeiro", "Capcioso"], GOLPE, 20, "Laço e Guia",
                 "3 de Resistência. Aproxime-se 1 pernada de uma criatura ou traga um parça 1 pernada para perto de você."),
    "Cutelo": (["Poderoso", "Preciso"], GOLPE, 20, "Corte Limpo",
               "4 ações. Faça um Golpe Poderoso ou Preciso a até 1 pernada. Sucesso: 2 × [A] de dano à Parte. Falha: você fica Exposto."),
    "Espeto": (["Preciso", "Ligeiro"], GOLPE, 20, "Rajada de Movimento",
               "5 de Resistência. Ganhe 1 ação extra durante a Caçada."),
    "Luvas": (["Poderoso", "Ligeiro"], GOLPE, 20, "De Perto",
              "Passiva. Seus Golpes contra criaturas a 0 pernadas têm Vantagem."),
    "Maçarico": (["Preciso", "Capcioso"], "1 (Golpe), 3 (Tiro)", 20, "Linha de Fogo",
                 "Passiva. Acrescenta alcance de 3 pernadas para Tiro."),
    "Panela": (["Poderoso", "Capcioso"], GOLPE, 50, "Escudo de Aço",
                "Passiva. Aumenta a durabilidade máxima da Panela em 30."),
}

utensilio = sa.table("utensilio", sa.column("id"), sa.column("nome"), sa.column("usuario_id"),
                     sa.column("disponivel_na_criacao"), sa.column("alcance"),
                     sa.column("durabilidade_max"), sa.column("estilos_principais", sa.JSON()))
tecnica = sa.table("tecnica", sa.column("id", sa.Integer()), sa.column("nome"), sa.column("descricao"))
vinculo = sa.table("utensilio_tecnica", sa.column("utensilio_id"), sa.column("tecnica_id"))
inventario = sa.table("feral_inventario", sa.column("utensilio_id"), sa.column("durabilidade_atual"))


def modelos_oficiais(nome):
    return sa.select(utensilio.c.id, utensilio.c.durabilidade_max).where(
        utensilio.c.nome == nome, utensilio.c.usuario_id.is_(None), utensilio.c.disponivel_na_criacao
    )


def id_tecnica(db, nome, descricao):
    return db.scalar(sa.select(tecnica.c.id).where(
        tecnica.c.nome == nome, tecnica.c.descricao == descricao
    ).order_by(tecnica.c.id).limit(1))


def atualizar_durabilidade(db, utensilio_id, delta):
    atual = inventario.c.durabilidade_atual
    nova = atual + delta
    db.execute(inventario.update().where(
        inventario.c.utensilio_id == utensilio_id, atual > 0
    ).values(durabilidade_atual=sa.case((nova < 1, 1), else_=nova)))


def upgrade():
    op.add_column("utensilio", sa.Column("estilos_principais", sa.JSON(), nullable=True))
    db = op.get_bind()
    for nome, (estilos, alcance, maximo, titulo, descricao) in MODELOS.items():
        modelos = db.execute(modelos_oficiais(nome)).all()
        if not modelos:
            continue
        tecnica_id = id_tecnica(db, titulo, descricao)
        if tecnica_id is None:
            tecnica_id = db.scalar(tecnica.insert().values(nome=titulo, descricao=descricao).returning(tecnica.c.id))
        for modelo_id, maximo_anterior in modelos:
            db.execute(utensilio.update().where(utensilio.c.id == modelo_id).values(
                estilos_principais=estilos, alcance=alcance, durabilidade_max=maximo
            ))
            atualizar_durabilidade(db, modelo_id, maximo - maximo_anterior)
            condicao = (vinculo.c.utensilio_id == modelo_id, vinculo.c.tecnica_id == tecnica_id)
            if db.scalar(sa.select(vinculo.c.tecnica_id).where(*condicao)) is None:
                db.execute(vinculo.insert().values(utensilio_id=modelo_id, tecnica_id=tecnica_id))


def downgrade():
    db = op.get_bind()
    for nome, (_, _, _, titulo, descricao) in MODELOS.items():
        tecnica_id = id_tecnica(db, titulo, descricao)
        for modelo_id, maximo in db.execute(modelos_oficiais(nome)).all():
            atualizar_durabilidade(db, modelo_id, 20 - maximo)
            db.execute(vinculo.delete().where(
                vinculo.c.utensilio_id == modelo_id, vinculo.c.tecnica_id == tecnica_id
            ))
            db.execute(utensilio.update().where(utensilio.c.id == modelo_id).values(
                alcance="1 (Golpear)", durabilidade_max=20
            ))
    op.drop_column("utensilio", "estilos_principais")
