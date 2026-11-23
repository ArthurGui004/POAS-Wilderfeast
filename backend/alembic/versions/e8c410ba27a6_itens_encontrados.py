"""Cria o inventário de itens encontrados por cada Feral."""

import sqlalchemy as sa
from alembic import op

revision = "e8c410ba27a6"
down_revision = "9e34b89c274a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "feral_item_encontrado",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("feral_id", sa.Integer(), sa.ForeignKey("feral.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.Text()),
        sa.CheckConstraint("quantidade > 0", name="ck_item_encontrado_quantidade"),
    )
    op.create_index("ix_feral_item_encontrado_feral_id", "feral_item_encontrado", ["feral_id"])


def downgrade():
    op.drop_table("feral_item_encontrado")
