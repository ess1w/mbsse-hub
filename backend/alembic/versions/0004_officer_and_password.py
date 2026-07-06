"""GEM district officer role, forced password change, GEM review

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-06

  - users: + must_change_password, + district_id (FK districts), role widened to
    VARCHAR(30) to fit 'gem_district_officer'
  - gem_reports: + reviewed_by, + reviewed_at, and a new 'reviewed' status value
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────
    op.alter_column('users', 'role',
        existing_type=sa.String(20), type_=sa.String(30), existing_nullable=False)
    op.add_column('users', sa.Column(
        'must_change_password', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('users', sa.Column('district_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'users_district_id_fkey', 'users', 'districts',
        ['district_id'], ['id'], ondelete='SET NULL')

    # ── gem_reports ───────────────────────────────────────────────────────
    op.add_column('gem_reports', sa.Column(
        'reviewed_by', postgresql.UUID(as_uuid=True),
        sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('gem_reports', sa.Column(
        'reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True))

    # New enum value must be added outside a transaction block
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE gem_submission_status ADD VALUE IF NOT EXISTS 'reviewed'")


def downgrade() -> None:
    op.drop_column('gem_reports', 'reviewed_at')
    op.drop_column('gem_reports', 'reviewed_by')
    # (the 'reviewed' enum value is left in place — removing a PG enum value
    #  requires recreating the type and is not reversible here.)

    op.drop_constraint('users_district_id_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'district_id')
    op.drop_column('users', 'must_change_password')
    op.alter_column('users', 'role',
        existing_type=sa.String(30), type_=sa.String(20), existing_nullable=False)
