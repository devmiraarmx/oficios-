"""Agregar Aluminero al catálogo y la opción "Otro" (oficio escrito a mano)

Revision ID: d4e8a2f6b1c9
Revises: b7d3f5a8c2e4
Create Date: 2026-11-17

- Siembra idempotente de "Aluminero" en la sección Acabados.
- Columna `profesionales.oficio_otro`: cuando el oficio del profesional no
  está en el catálogo (ej. "Especialista en hidroneumáticos"), lo escribe a
  mano. No se crea un oficio nuevo; los socios lo ven en el panel y deciden
  si lo agregan al catálogo.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e8a2f6b1c9'
down_revision = 'b7d3f5a8c2e4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('profesionales', schema=None) as batch_op:
        batch_op.add_column(sa.Column('oficio_otro', sa.String(length=120), nullable=True))

    bind = op.get_bind()
    existe = bind.execute(
        sa.text("SELECT 1 FROM oficios WHERE slug = 'aluminero' OR nombre = 'Aluminero'")
    ).first()
    if not existe:
        bind.execute(sa.text(
            "INSERT INTO oficios (nombre, slug, categoria, seccion) "
            "VALUES ('Aluminero', 'aluminero', 'oficio', 'acabados')"
        ))
    else:
        bind.execute(sa.text(
            "UPDATE oficios SET seccion = 'acabados' "
            "WHERE slug = 'aluminero' AND seccion IS NULL"
        ))


def downgrade():
    bind = op.get_bind()
    # Solo borra Aluminero si ningún profesional lo tiene asignado.
    bind.execute(sa.text(
        "DELETE FROM oficios WHERE slug = 'aluminero' AND id NOT IN "
        "(SELECT oficio_id FROM profesional_oficios)"
    ))
    with op.batch_alter_table('profesionales', schema=None) as batch_op:
        batch_op.drop_column('oficio_otro')
