"""Add '19 and older' age band to output_indicators

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-08

Adds students_inschool_age_19_plus and students_oos_age_19_plus columns so the
Partner Reporting form can capture students reached who are 19 and older.
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('output_indicators',
                  sa.Column('students_inschool_age_19_plus', sa.Integer(), server_default='0', nullable=True))
    op.add_column('output_indicators',
                  sa.Column('students_oos_age_19_plus', sa.Integer(), server_default='0', nullable=True))


def downgrade():
    op.drop_column('output_indicators', 'students_oos_age_19_plus')
    op.drop_column('output_indicators', 'students_inschool_age_19_plus')
