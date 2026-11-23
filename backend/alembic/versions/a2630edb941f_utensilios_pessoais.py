"""Os utensílios já cadastrados continuam no catálogo comum."""
from alembic import op
import sqlalchemy as sa

revision = "a2630edb941f"
down_revision = "74a10cbe2410"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("utensilio") as table:
        table.add_column(sa.Column("usuario_id", sa.Integer(), nullable=True))
        table.create_foreign_key("fk_utensilio_usuario", "usuario", ["usuario_id"], ["id"], ondelete="CASCADE")


def downgrade():
    pessoal = op.get_bind().execute(sa.text(
        "SELECT 1 FROM utensilio WHERE usuario_id IS NOT NULL LIMIT 1"
    )).first()
    if pessoal:
        raise RuntimeError("O catálogo contém utensílios pessoais. A reversão os tornaria públicos.")
    with op.batch_alter_table("utensilio") as table:
        table.drop_constraint("fk_utensilio_usuario", type_="foreignkey")
        table.drop_column("usuario_id")
