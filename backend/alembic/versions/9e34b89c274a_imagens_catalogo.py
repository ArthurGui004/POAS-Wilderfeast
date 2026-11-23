"""Adiciona as URLs das imagens ao catálogo."""

import sqlalchemy as sa
from alembic import op

revision = "9e34b89c274a"
down_revision = "0cdfe3edc196"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("monstro", sa.Column("imagem_url", sa.Text(), nullable=True))
    op.add_column("utensilio", sa.Column("imagem_url", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("utensilio", "imagem_url")
    op.drop_column("monstro", "imagem_url")
