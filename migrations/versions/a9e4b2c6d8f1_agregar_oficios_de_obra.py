"""Sembrar oficios de obra (yesero, herrero, fierrero, cimbrador...)

Revision ID: a9e4b2c6d8f1
Revises: c3d7e9a1b5f2
Create Date: 2026-10-08

Los socios pidieron ampliar el catálogo porque trabajadores como yeseros o
tablaroqueros no encontraban su oficio al registrarse. Siembra idempotente
(solo inserta el oficio que no exista por slug), igual que la migración de
especialistas, para que aparezcan en producción sin correr `seed`.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9e4b2c6d8f1'
down_revision = 'c3d7e9a1b5f2'
branch_labels = None
depends_on = None


OFICIOS_OBRA = [
    ("Herrero", "herrero"),
    ("Yesero", "yesero"),
    ("Colocador de Pisos y Azulejos", "colocador-pisos-azulejos"),
    ("Pastero", "pastero"),
    ("Estuquero", "estuquero"),
    ("Bloquero", "bloquero"),
    ("Tablaroquero", "tablaroquero"),
    ("Instalador de Sistemas contra Incendios", "sistemas-contra-incendios"),
    ("Carpintero de Obra", "carpintero-de-obra"),
    ("Fierrero", "fierrero"),
    ("Colador", "colador"),
    ("Cimbrador", "cimbrador"),
]


def upgrade():
    bind = op.get_bind()
    for nombre, slug in OFICIOS_OBRA:
        existe = bind.execute(
            sa.text("SELECT 1 FROM oficios WHERE slug = :slug OR nombre = :nombre"),
            {"slug": slug, "nombre": nombre},
        ).first()
        if not existe:
            bind.execute(
                sa.text(
                    "INSERT INTO oficios (nombre, slug, categoria) "
                    "VALUES (:nombre, :slug, 'oficio')"
                ),
                {"nombre": nombre, "slug": slug},
            )


def downgrade():
    # Solo borra los oficios que ningún profesional tenga asignado.
    bind = op.get_bind()
    for _nombre, slug in OFICIOS_OBRA:
        bind.execute(
            sa.text(
                "DELETE FROM oficios WHERE slug = :slug AND id NOT IN "
                "(SELECT oficio_id FROM profesional_oficios)"
            ),
            {"slug": slug},
        )
