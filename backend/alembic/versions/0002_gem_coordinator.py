"""GEM Coordinator monthly reporting tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-10

Adds:
  - gem_coordinator value to user_role enum
  - gem_reports table (one row per monthly submission)
  - gem_report_activities junction table (multi-select activities)
  - gem_report_key_messages junction table (multi-select key messages)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extend user_role enum ─────────────────────────────────────────────
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'gem_coordinator'")

    # ── New enums ─────────────────────────────────────────────────────────
    gem_impl_status = postgresql.ENUM(
        'Fully', 'Partially', 'Not implemented',
        name='gem_impl_status', create_type=False,
    )
    gem_impl_status.create(op.get_bind(), checkfirst=True)

    gem_impl_reason = postgresql.ENUM(
        'Lack of funds', 'Low participation', 'Weather/logistics',
        'School schedule conflict', 'Lack of materials', 'Other',
        name='gem_impl_reason', create_type=False,
    )
    gem_impl_reason.create(op.get_bind(), checkfirst=True)

    gem_submission_status = postgresql.ENUM(
        'draft', 'submitted',
        name='gem_submission_status', create_type=False,
    )
    gem_submission_status.create(op.get_bind(), checkfirst=True)

    # ── gem_reports ───────────────────────────────────────────────────────
    op.create_table(
        'gem_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),

        # Section 1: Basic Information
        sa.Column('reporting_month', sa.Date(), nullable=False),   # first day of month
        sa.Column('district_id', sa.Integer(),
                  sa.ForeignKey('districts.id'), nullable=False),
        sa.Column('coordinator_name', sa.String(120), nullable=False),
        sa.Column('schools_covered', sa.Integer(), nullable=False,
                  server_default='0'),

        # Section 2: Activity Implementation
        sa.Column('total_activities', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('impl_status', postgresql.ENUM(
            'Fully', 'Partially', 'Not implemented',
            name='gem_impl_status', create_type=False,
        ), nullable=False),
        sa.Column('impl_reason', postgresql.ENUM(
            'Lack of funds', 'Low participation', 'Weather/logistics',
            'School schedule conflict', 'Lack of materials', 'Other',
            name='gem_impl_reason', create_type=False,
        ), nullable=True),
        sa.Column('impl_reason_other', sa.Text(), nullable=True),

        # Section 3: Reach
        sa.Column('total_participants', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('girls_reached', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('boys_reached', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('teachers_parents_community', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('teenage_girls', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('children_disability', sa.Integer(), nullable=False,
                  server_default='0'),

        # Section 4: Key Outputs
        sa.Column('functional_clubs', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('srgbv_referrals', sa.Integer(), nullable=False,
                  server_default='0'),

        # Section 5: Challenges
        sa.Column('main_challenge', sa.Text(), nullable=True),

        # Status / timestamps
        sa.Column('status', postgresql.ENUM(
            'draft', 'submitted',
            name='gem_submission_status', create_type=False,
        ), nullable=False, server_default='draft'),
        sa.Column('submitted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.func.now()),
    )

    op.create_index('idx_gem_reports_district', 'gem_reports', ['district_id'])
    op.create_index('idx_gem_reports_month', 'gem_reports', ['reporting_month'])
    op.create_index('idx_gem_reports_submitted_by', 'gem_reports', ['submitted_by'])

    # ── gem_report_activities ─────────────────────────────────────────────
    op.create_table(
        'gem_report_activities',
        sa.Column('report_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('gem_reports.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('activity', sa.String(80), nullable=False),
        sa.Column('activity_other', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('report_id', 'activity'),
    )

    # ── gem_report_key_messages ───────────────────────────────────────────
    op.create_table(
        'gem_report_key_messages',
        sa.Column('report_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('gem_reports.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('message', sa.String(80), nullable=False),
        sa.Column('message_other', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('report_id', 'message'),
    )


def downgrade() -> None:
    op.drop_table('gem_report_key_messages')
    op.drop_table('gem_report_activities')
    op.drop_index('idx_gem_reports_submitted_by', 'gem_reports')
    op.drop_index('idx_gem_reports_month', 'gem_reports')
    op.drop_index('idx_gem_reports_district', 'gem_reports')
    op.drop_table('gem_reports')
    op.execute("DROP TYPE IF EXISTS gem_submission_status")
    op.execute("DROP TYPE IF EXISTS gem_impl_reason")
    op.execute("DROP TYPE IF EXISTS gem_impl_status")
    # Note: cannot remove a value from a Postgres enum — gem_coordinator remains in user_role
