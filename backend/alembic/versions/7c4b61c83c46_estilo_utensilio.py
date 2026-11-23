"""Guarda o estilo de três pontos escolhido para o utensílio equipado."""

import sqlalchemy as sa
from alembic import op

revision = "7c4b61c83c46"
down_revision = "e8c410ba27a6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("feral_inventario", sa.Column("estilo_escolhido", sa.String(100)))


def downgrade():
    op.drop_column("feral_inventario", "estilo_escolhido")
