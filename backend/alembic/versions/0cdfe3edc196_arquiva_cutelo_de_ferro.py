"""Retira o Cutelo de Ferro do catálogo, preservando eventuais fichas antigas."""

import sqlalchemy as sa
from alembic import op

revision = "0cdfe3edc196"
down_revision = "d1c641bf980e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("utensilio", sa.Column("arquivado", sa.Boolean(), nullable=False, server_default=sa.false()))
    utensilio = sa.table(
        "utensilio",
        sa.column("nome", sa.String()),
        sa.column("usuario_id", sa.Integer()),
        sa.column("arquivado", sa.Boolean()),
    )
    op.execute(utensilio.update().where(
        utensilio.c.nome == op.inline_literal("Cutelo de Ferro"),
        utensilio.c.usuario_id.is_(None),
    ).values(arquivado=sa.true()))


def downgrade():
    op.drop_column("utensilio", "arquivado")
