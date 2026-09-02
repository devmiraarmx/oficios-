"""Agregar tabla derivaciones (asignación manual de un lead a un profesional)

Revision ID: c3d7e9a1b5f2
Revises: f2a1c9d4b7e3
Create Date: 2026-09-02

Registra cuando un socio/admin deriva una solicitud a un profesional concreto.
El profesional ve ese lead con el contacto revelado sin gastar créditos.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d7e9a1b5f2'
down_revision = 'f2a1c9d4b7e3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'derivaciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profesional_id', sa.Integer(), nullable=False),
        sa.Column('solicitud_id', sa.Integer(), nullable=False),
        sa.Column('creado_en', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['profesional_id'], ['profesionales.id'], ),
        sa.ForeignKeyConstraint(['solicitud_id'], ['solicitudes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profesional_id', 'solicitud_id', name='uq_derivacion_prof_sol'),
    )
    with op.batch_alter_table('derivaciones', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_derivaciones_profesional_id'), ['profesional_id'], unique=False)
        batch_op.create_index(
            batch_op.f('ix_derivaciones_solicitud_id'), ['solicitud_id'], unique=False)


def downgrade():
    with op.batch_alter_table('derivaciones', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_derivaciones_solicitud_id'))
        batch_op.drop_index(batch_op.f('ix_derivaciones_profesional_id'))
    op.drop_table('derivaciones')
