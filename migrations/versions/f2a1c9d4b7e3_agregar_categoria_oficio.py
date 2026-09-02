"""Agregar columna categoria a oficios y sembrar especialistas

Revision ID: f2a1c9d4b7e3
Revises: 0b628ed903d1
Create Date: 2026-09-02

- Agrega la columna `categoria` a `oficios` para agrupar el catálogo en
  secciones: 'oficio' (plomero, albañil...) y 'especialista' (arquitecto,
  ingeniero...). Las filas existentes quedan como 'oficio' por el
  server_default.
- Siembra los especialistas iniciales de forma idempotente (solo inserta el
  que no exista por slug), para que aparezcan en producción sin correr el
  comando `seed` (Railway solo ejecuta `flask db upgrade` al arrancar).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2a1c9d4b7e3'
down_revision = '0b628ed903d1'
branch_labels = None
depends_on = None


ESPECIALISTAS = [
    ("Arquitecto", "arquitecto"),
    ("Ingeniero Civil", "ingeniero-civil"),
    ("Ingeniero Eléctrico", "ingeniero-electrico"),
    ("Topógrafo", "topografo"),
    ("Diseñador de Interiores", "disenador-interiores"),
    ("Perito / DRO", "perito-dro"),
]


def upgrade():
    with op.batch_alter_table('oficios', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('categoria', sa.String(length=20), nullable=False,
                      server_default='oficio')
        )

    # Siembra idempotente de especialistas (no duplica si ya existen).
    bind = op.get_bind()
    for nombre, slug in ESPECIALISTAS:
        existe = bind.execute(
            sa.text("SELECT 1 FROM oficios WHERE slug = :slug"),
            {"slug": slug},
        ).first()
        if not existe:
            bind.execute(
                sa.text(
                    "INSERT INTO oficios (nombre, slug, categoria) "
                    "VALUES (:nombre, :slug, 'especialista')"
                ),
                {"nombre": nombre, "slug": slug},
            )


def downgrade():
    # Elimina los especialistas sembrados por esta migración y quita la columna.
    bind = op.get_bind()
    for _nombre, slug in ESPECIALISTAS:
        bind.execute(
            sa.text("DELETE FROM oficios WHERE slug = :slug AND categoria = 'especialista'"),
            {"slug": slug},
        )
    with op.batch_alter_table('oficios', schema=None) as batch_op:
        batch_op.drop_column('categoria')
