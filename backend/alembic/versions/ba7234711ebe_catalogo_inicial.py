"""Distingue opções iniciais de itens já existentes no inventário."""
from alembic import op
import sqlalchemy as sa

revision = "ba7234711ebe"
down_revision = "a2630edb941f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("utensilio", sa.Column("disponivel_na_criacao", sa.Boolean(), nullable=False, server_default=sa.false()))
    utensilio = sa.table(
        "utensilio", sa.column("nome", sa.String()), sa.column("alcance", sa.String()),
        sa.column("durabilidade_max", sa.Integer()), sa.column("disponivel_na_criacao", sa.Boolean()),
    )
    op.bulk_insert(utensilio, [
        {"nome": nome, "alcance": "1 (Golpear)", "durabilidade_max": 20, "disponivel_na_criacao": True}
        for nome in ("Barbante", "Cutelo", "Espeto", "Luvas", "Maçarico", "Panela")
    ])


def downgrade():
    # Itens em uso ficam disponíveis para leitura pelos clientes da versão anterior.
    op.execute("DELETE FROM utensilio WHERE disponivel_na_criacao AND NOT EXISTS "
               "(SELECT 1 FROM feral_inventario WHERE utensilio_id = utensilio.id)")
    with op.batch_alter_table("utensilio") as table:
        table.drop_column("disponivel_na_criacao")
