"""form_template_facilitator

Revision ID: c2d3e4f5a6b7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-27 10:00:00.000000

Adds template/clone system and facilitator fields to forms table.
"""
from alembic import op
import sqlalchemy as sa

revision = 'c2d3e4f5a6b7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('forms', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_template',      sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('cloned_from',      sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('facilitator_name', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('facilitator_id',   sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_forms_cloned_from', 'forms',  ['cloned_from'],    ['id'])
        batch_op.create_foreign_key('fk_forms_facilitator', 'users',  ['facilitator_id'], ['id'])


def downgrade():
    with op.batch_alter_table('forms', schema=None) as batch_op:
        batch_op.drop_constraint('fk_forms_facilitator', type_='foreignkey')
        batch_op.drop_constraint('fk_forms_cloned_from', type_='foreignkey')
        batch_op.drop_column('facilitator_id')
        batch_op.drop_column('facilitator_name')
        batch_op.drop_column('cloned_from')
        batch_op.drop_column('is_template')
