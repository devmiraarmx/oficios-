"""Agrupar oficios por sección (obra negra, acabados, instalaciones...)

Revision ID: b7d3f5a8c2e4
Revises: a9e4b2c6d8f1
Create Date: 2026-10-08

Con el catálogo ampliado, el inicio y el registro mostraban un muro de
botones. Agrega la columna `seccion` a `oficios` y clasifica los oficios
existentes por slug. Un oficio que quede sin sección se muestra en
"Otros oficios", así que no se pierde ninguno.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7d3f5a8c2e4'
down_revision = 'a9e4b2c6d8f1'
branch_labels = None
depends_on = None


SECCION_POR_SLUG = {
    # Obra negra y estructura
    "albanil": "obra_negra",
    "bloquero": "obra_negra",
    "fierrero": "obra_negra",
    "cimbrador": "obra_negra",
    "colador": "obra_negra",
    # Acabados
    "yesero": "acabados",
    "pastero": "acabados",
    "estuquero": "acabados",
    "tablaroquero": "acabados",
    "colocador-pisos-azulejos": "acabados",
    "pintor": "acabados",
    # Instalaciones
    "plomero": "instalaciones",
    "electricista": "instalaciones",
    "sistemas-contra-incendios": "instalaciones",
    # Carpintería, herrería y cerrajería
    "carpintero": "carpinteria_herreria",
    "carpintero-de-obra": "carpinteria_herreria",
    "herrero": "carpinteria_herreria",
    "cerrajero": "carpinteria_herreria",
}


def upgrade():
    with op.batch_alter_table('oficios', schema=None) as batch_op:
        batch_op.add_column(sa.Column('seccion', sa.String(length=30), nullable=True))

    bind = op.get_bind()
    for slug, seccion in SECCION_POR_SLUG.items():
        bind.execute(
            sa.text(
                "UPDATE oficios SET seccion = :seccion "
                "WHERE slug = :slug AND categoria = 'oficio'"
            ),
            {"slug": slug, "seccion": seccion},
        )


def downgrade():
    with op.batch_alter_table('oficios', schema=None) as batch_op:
        batch_op.drop_column('seccion')
