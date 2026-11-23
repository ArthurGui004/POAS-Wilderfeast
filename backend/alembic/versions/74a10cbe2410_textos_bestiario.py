"""Permite guardar descrições completas das fichas do bestiário."""
from alembic import op
import sqlalchemy as sa

revision = "74a10cbe2410"
down_revision = "599d684d1d62"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("monstro") as table:
        table.alter_column("dieta", existing_type=sa.String(100), type_=sa.Text())
        table.alter_column("habitat", existing_type=sa.String(100), type_=sa.Text())
    with op.batch_alter_table("monstro_parte") as table:
        table.alter_column("alcance", existing_type=sa.String(50), type_=sa.Text())
        table.alter_column("se_quebrado", existing_type=sa.String(100), type_=sa.Text())


def downgrade():
    with op.batch_alter_table("monstro_parte") as table:
        table.alter_column("se_quebrado", existing_type=sa.Text(), type_=sa.String(100))
        table.alter_column("alcance", existing_type=sa.Text(), type_=sa.String(50))
    with op.batch_alter_table("monstro") as table:
        table.alter_column("habitat", existing_type=sa.Text(), type_=sa.String(100))
        table.alter_column("dieta", existing_type=sa.Text(), type_=sa.String(100))
