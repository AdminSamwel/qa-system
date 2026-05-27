"""NACTVET QEI fields, director/ceo roles, ReportAcknowledgement

Revision ID: a1b2c3d4e5f6
Revises: 6317c22d7e11
Create Date: 2026-05-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '6317c22d7e11'
branch_labels = None
depends_on = None


def upgrade():
    # ── users ──────────────────────────────────────────────────────────────
    with op.batch_alter_table('users') as batch:
        batch.add_column(sa.Column('phone', sa.String(20), nullable=True))
        batch.add_column(sa.Column('title', sa.String(50), nullable=True))

    # ── campuses ───────────────────────────────────────────────────────────
    with op.batch_alter_table('campuses') as batch:
        batch.add_column(sa.Column('contact_email', sa.String(120), nullable=True))
        batch.add_column(sa.Column('contact_phone', sa.String(20),  nullable=True))

    # ── programmes ─────────────────────────────────────────────────────────
    with op.batch_alter_table('programmes') as batch:
        batch.add_column(sa.Column('nta_level', sa.String(20), nullable=True))

    # ── courses ────────────────────────────────────────────────────────────
    with op.batch_alter_table('courses') as batch:
        batch.add_column(sa.Column('target_audience', sa.String(20),
                                   server_default='students', nullable=True))
        batch.add_column(sa.Column('contact_hours', sa.Integer, nullable=True))

    # ── forms ──────────────────────────────────────────────────────────────
    with op.batch_alter_table('forms') as batch:
        batch.add_column(sa.Column('form_type', sa.String(20),
                                   server_default='standard', nullable=True))
        batch.add_column(sa.Column('nactvet_version', sa.String(10),
                                   server_default='2023', nullable=True))
        batch.add_column(sa.Column('policy_ref', sa.String(100), nullable=True))

    # ── form_sections ──────────────────────────────────────────────────────
    with op.batch_alter_table('form_sections') as batch:
        batch.add_column(sa.Column('naqs_reference', sa.String(50), nullable=True))
        batch.add_column(sa.Column('ideal_score',    sa.Float,
                                   server_default='5.0', nullable=True))

    # ── form_questions ─────────────────────────────────────────────────────
    with op.batch_alter_table('form_questions') as batch:
        batch.add_column(sa.Column('naqs_reference', sa.String(50), nullable=True))

    # ── evaluations ────────────────────────────────────────────────────────
    with op.batch_alter_table('evaluations') as batch:
        batch.add_column(sa.Column('participant_type',  sa.String(20),
                                   server_default='student', nullable=True))
        batch.add_column(sa.Column('participant_name',  sa.String(100), nullable=True))
        batch.add_column(sa.Column('participant_org',   sa.String(150), nullable=True))
        batch.add_column(sa.Column('participant_email', sa.String(120), nullable=True))
        batch.alter_column('overall_score',
                           existing_type=sa.Integer,
                           type_=sa.Float,
                           existing_nullable=True)

    # ── report_acknowledgements (new table) ────────────────────────────────
    op.create_table(
        'report_acknowledgements',
        sa.Column('id',              sa.Integer,  primary_key=True),
        sa.Column('course_id',       sa.Integer,  sa.ForeignKey('courses.id'),  nullable=False),
        sa.Column('acknowledged_by', sa.Integer,  sa.ForeignKey('users.id'),   nullable=False),
        sa.Column('acknowledged_at', sa.DateTime, nullable=True),
        sa.Column('notes',           sa.Text,     nullable=True),
        sa.Column('action_required', sa.Boolean,  server_default='false', nullable=True),
        sa.Column('role',            sa.String(20), nullable=False),
    )


def downgrade():
    op.drop_table('report_acknowledgements')

    with op.batch_alter_table('evaluations') as batch:
        batch.drop_column('participant_email')
        batch.drop_column('participant_org')
        batch.drop_column('participant_name')
        batch.drop_column('participant_type')

    with op.batch_alter_table('form_questions') as batch:
        batch.drop_column('naqs_reference')

    with op.batch_alter_table('form_sections') as batch:
        batch.drop_column('ideal_score')
        batch.drop_column('naqs_reference')

    with op.batch_alter_table('forms') as batch:
        batch.drop_column('policy_ref')
        batch.drop_column('nactvet_version')
        batch.drop_column('form_type')

    with op.batch_alter_table('courses') as batch:
        batch.drop_column('contact_hours')
        batch.drop_column('target_audience')

    with op.batch_alter_table('programmes') as batch:
        batch.drop_column('nta_level')

    with op.batch_alter_table('campuses') as batch:
        batch.drop_column('contact_phone')
        batch.drop_column('contact_email')

    with op.batch_alter_table('users') as batch:
        batch.drop_column('title')
        batch.drop_column('phone')
