"""initial schema v3

Revision ID: 0001
Revises:
Create Date: 2026-05-19

Full schema rebuild based on data dictionary Sections 5.1-5.7.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Reference tables ──────────────────────────────────────────────────
    op.create_table(
        'districts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('region_name', sa.String(40)),
        sa.Column('district_name', sa.String(60), nullable=False, unique=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'chiefdoms',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('district_id', sa.Integer(), sa.ForeignKey('districts.id'), nullable=False),
        sa.Column('chiefdom_name', sa.String(80), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Organisation registry (Section 5.1) ──────────────────────────────
    op.create_table(
        'organisations',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_name', sa.String(200), nullable=False, unique=True),
        sa.Column('org_type', sa.String(40), nullable=False),        # CSO / UN Agency / Government / Other
        sa.Column('focal_person', sa.String(120)),
        sa.Column('email', sa.String(254)),
        sa.Column('phone', sa.String(30)),
        sa.Column('sla_signed', sa.Boolean(), nullable=False, default=False),
        sa.Column('registration_date', sa.Date(), server_default=sa.func.current_date()),
        sa.Column('status', sa.String(20), nullable=False, server_default='Pending'),  # Active/Inactive/Pending
        sa.Column('acronym', sa.String(30)),
        sa.Column('districts', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Project registry (Section 5.2) ───────────────────────────────────
    op.create_table(
        'projects',
        sa.Column('project_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.org_id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_title', sa.String(300), nullable=False),
        sa.Column('project_start', sa.Date()),
        sa.Column('project_end', sa.Date()),
        sa.Column('objective', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('tactic', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('focus_area', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('activity_summary', sa.Text()),
        sa.Column('funding_source', sa.String(300)),
        sa.Column('budget_usd', sa.Numeric(14, 2)),
        sa.Column('budget_currency', sa.String(3), server_default='USD'),
        sa.Column('gov_counterpart', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('key_partners', sa.Text()),
        sa.Column('project_status', sa.String(20), server_default='Active'),  # Active/Closed/Planned
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_projects_org_id', 'projects', ['org_id'])

    # ── Auth ──────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(254), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(120), nullable=False),
        sa.Column('role', sa.String(10), nullable=False, server_default='partner'),  # admin|viewer|partner
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.org_id', ondelete='SET NULL')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_login', sa.TIMESTAMP(timezone=True)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'token_blacklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('jti', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Reporting periods ─────────────────────────────────────────────────
    op.create_table(
        'reporting_periods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('label', sa.String(40), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('deadline', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # ── Submissions ───────────────────────────────────────────────────────
    op.create_table(
        'submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.org_id'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.project_id'), nullable=False),
        sa.Column('reporting_period_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reporting_periods.id'), nullable=False),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),  # draft/submitted/verified

        # Section F
        sa.Column('key_results', sa.Text()),
        sa.Column('observed_changes', sa.Text()),
        sa.Column('early_outcomes', sa.Text()),

        # Section G
        sa.Column('expenditure', sa.Numeric(14, 2)),
        sa.Column('expenditure_currency', sa.String(3), server_default='USD'),
        sa.Column('budget_util', sa.String(30)),

        # Section H
        sa.Column('gov_engaged', sa.Boolean()),
        sa.Column('gov_engaged_list', sa.Text()),
        sa.Column('coordination_meetings', sa.Integer(), server_default='0'),
        sa.Column('key_partners', sa.Text()),

        # Section I
        sa.Column('challenges', sa.Text()),
        sa.Column('risks', sa.Text()),
        sa.Column('mitigations', sa.Text()),

        # Section J — safeguarding (access-controlled)
        sa.Column('safeguarding_cases', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cases_reported', sa.Integer(), server_default='0'),
        sa.Column('cases_referred', sa.Integer(), server_default='0'),
        sa.Column('referral_pathway', sa.String(120)),
        sa.Column('safeguarding_action', sa.Text()),

        # Section L
        sa.Column('planned_activities', sa.Text()),
        sa.Column('support_needed', sa.Text()),

        # Section M — admin review
        sa.Column('review_flag', sa.String(40)),
        sa.Column('review_notes', sa.Text()),

        sa.Column('submitted_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('verified_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_submissions_org_id', 'submissions', ['org_id'])
    op.create_index('ix_submissions_period_id', 'submissions', ['reporting_period_id'])

    # ── Submission locations (Section 5.6) ────────────────────────────────
    op.create_table(
        'submission_locations',
        sa.Column('location_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('district_name', sa.String(60), nullable=False),
        sa.Column('chiefdom_name', sa.String(80)),
        sa.Column('community_name', sa.String(120)),
        sa.Column('school_name', sa.String(200)),
        sa.Column('emis_code', sa.String(20)),
        sa.Column('gps_lat', sa.Float()),
        sa.Column('gps_lon', sa.Float()),
    )
    op.create_index('ix_submission_locations_submission_id', 'submission_locations', ['submission_id'])

    # ── Activities (Section 5.5) ──────────────────────────────────────────
    op.create_table(
        'activities',
        sa.Column('activity_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('focus_areas', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('objectives', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('tactics', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('activity_type', sa.String(80)),
        sa.Column('intervention_levels', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('activity_title', sa.String(300)),
        sa.Column('description', sa.Text()),
        sa.Column('planned_vs_actual', sa.String(20)),
        sa.Column('implementation_status', sa.String(20)),
        sa.Column('start_date', sa.Date()),
        sa.Column('end_date', sa.Date()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_activities_submission_id', 'activities', ['submission_id'])

    # ── Output indicators (Section 5.7) ───────────────────────────────────
    op.create_table(
        'output_indicators',
        sa.Column('activity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('activities.activity_id', ondelete='CASCADE'), primary_key=True),

        # Schools by level
        sa.Column('schools_pre_primary', sa.Integer(), server_default='0'),
        sa.Column('schools_primary', sa.Integer(), server_default='0'),
        sa.Column('schools_jss', sa.Integer(), server_default='0'),
        sa.Column('schools_sss', sa.Integer(), server_default='0'),

        # School SRGBV mechanisms
        sa.Column('schools_with_focal_person', sa.Integer(), server_default='0'),
        sa.Column('schools_with_reporting_protocol', sa.Integer(), server_default='0'),
        sa.Column('schools_with_referral_pathway', sa.Integer(), server_default='0'),
        sa.Column('schools_held_schoolwide_campaign', sa.Integer(), server_default='0'),
        sa.Column('schools_held_peer_led_session', sa.Integer(), server_default='0'),
        sa.Column('schools_with_safe_space', sa.Integer(), server_default='0'),

        # In-school students
        sa.Column('students_inschool_f', sa.Integer(), server_default='0'),
        sa.Column('students_inschool_m', sa.Integer(), server_default='0'),
        sa.Column('students_inschool_age_10_14', sa.Integer(), server_default='0'),
        sa.Column('students_inschool_age_15_19', sa.Integer(), server_default='0'),
        sa.Column('students_inschool_age_under10', sa.Integer(), server_default='0'),

        # Out-of-school students
        sa.Column('students_oos_f', sa.Integer(), server_default='0'),
        sa.Column('students_oos_m', sa.Integer(), server_default='0'),
        sa.Column('students_oos_age_10_14', sa.Integer(), server_default='0'),
        sa.Column('students_oos_age_15_19', sa.Integer(), server_default='0'),

        # Students with disability
        sa.Column('students_disability_f', sa.Integer(), server_default='0'),
        sa.Column('students_disability_m', sa.Integer(), server_default='0'),

        # Vulnerable groups
        sa.Column('pregnant_girls', sa.Integer(), server_default='0'),
        sa.Column('teenage_mothers', sa.Integer(), server_default='0'),

        # Student engagement
        sa.Column('students_used_reporting_mechanism', sa.Integer(), server_default='0'),
        sa.Column('students_confident_reporting', sa.Integer(), server_default='0'),

        # Teachers
        sa.Column('teachers_f', sa.Integer(), server_default='0'),
        sa.Column('teachers_m', sa.Integer(), server_default='0'),
        sa.Column('teachers_demonstrated_grp', sa.Integer(), server_default='0'),

        # District officials
        sa.Column('district_officials_f', sa.Integer(), server_default='0'),
        sa.Column('district_officials_m', sa.Integer(), server_default='0'),

        # Central officials
        sa.Column('central_officials_f', sa.Integer(), server_default='0'),
        sa.Column('central_officials_m', sa.Integer(), server_default='0'),

        # Community
        sa.Column('community_members_f', sa.Integer(), server_default='0'),
        sa.Column('community_members_m', sa.Integer(), server_default='0'),
        sa.Column('community_sessions', sa.Integer(), server_default='0'),

        # Policy
        sa.Column('policy_dialogue_events', sa.Integer(), server_default='0'),
    )

    # ── Supporting tables ─────────────────────────────────────────────────
    op.create_table(
        'uploaded_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('file_kind', sa.String(10), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('stored_key', sa.Text(), nullable=False, unique=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('storage_url', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'reminders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('reporting_period_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reporting_periods.id'), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.org_id'), nullable=False),
        sa.Column('sent_to_email', sa.String(254), nullable=False),
        sa.Column('reminder_type', sa.String(30), nullable=False),
        sa.Column('status', sa.String(10), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text()),
        sa.Column('scheduled_for', sa.TIMESTAMP(timezone=True)),
        sa.Column('sent_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('action', sa.String(60), nullable=False),
        sa.Column('resource_type', sa.String(60), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('diff', postgresql.JSONB()),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('reminders')
    op.drop_table('uploaded_files')
    op.drop_table('output_indicators')
    op.drop_table('activities')
    op.drop_table('submission_locations')
    op.drop_table('submissions')
    op.drop_table('reporting_periods')
    op.drop_table('token_blacklist')
    op.drop_table('users')
    op.drop_table('projects')
    op.drop_table('organisations')
    op.drop_table('chiefdoms')
    op.drop_table('districts')
