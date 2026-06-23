"""Partner Reporting Form amendments

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-23

Implements the client-requested form changes:
  - activities: + districts (Section C multi-district), + focus_area_other ("Other" free text)
  - output_indicators: + teenage_fathers; + district_name with composite PK
    (activity_id, district_name) so a full indicator set can be entered per district
  - training_by_focus_area: new table — teachers / officials trained, disaggregated
    by focus area, district and cadre
  - sla_documents: new table — org-level SLA uploads with admin approval workflow

Note: prior to this revision the submit-report endpoint never persisted activities
or output indicators, so those tables are effectively empty in production and the
output_indicators primary-key change carries no data-migration risk.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── activities: new Section C columns ─────────────────────────────────
    op.add_column('activities', sa.Column('focus_area_other', sa.Text(), nullable=True))
    op.add_column('activities', sa.Column('districts', postgresql.ARRAY(sa.String()), nullable=True))

    # ── output_indicators: new vulnerable-group column ────────────────────
    op.add_column('output_indicators', sa.Column('teenage_fathers', sa.Integer(), server_default='0', nullable=True))

    # ── output_indicators: per-district key ───────────────────────────────
    # Add district_name, then switch PK to the composite (activity_id, district_name).
    op.add_column('output_indicators',
        sa.Column('district_name', sa.String(60), nullable=False, server_default=''))
    op.drop_constraint('output_indicators_pkey', 'output_indicators', type_='primary')
    op.create_primary_key(
        'output_indicators_pkey', 'output_indicators', ['activity_id', 'district_name'])

    # ── training_by_focus_area: new table (#6) ────────────────────────────
    op.create_table(
        'training_by_focus_area',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('activity_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('activities.activity_id', ondelete='CASCADE'), nullable=False),
        sa.Column('district_name', sa.String(60), nullable=False, server_default=''),
        sa.Column('focus_area', sa.String(120), nullable=False),
        sa.Column('cadre', sa.String(20), nullable=False),   # teacher / district_official / central_official
        sa.Column('female', sa.Integer(), server_default='0'),
        sa.Column('male', sa.Integer(), server_default='0'),
    )
    op.create_index('idx_training_activity', 'training_by_focus_area', ['activity_id'])

    # ── sla_documents: new table (#8) ─────────────────────────────────────
    op.create_table(
        'sla_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('organisations.org_id', ondelete='CASCADE'), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('stored_key', sa.Text(), nullable=False, unique=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('storage_url', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_sla_org', 'sla_documents', ['org_id'])

    # Drop the temporary server defaults used only to backfill existing rows
    op.alter_column('output_indicators', 'district_name', server_default=None)


def downgrade() -> None:
    op.drop_index('idx_sla_org', 'sla_documents')
    op.drop_table('sla_documents')

    op.drop_index('idx_training_activity', 'training_by_focus_area')
    op.drop_table('training_by_focus_area')

    op.drop_constraint('output_indicators_pkey', 'output_indicators', type_='primary')
    op.create_primary_key('output_indicators_pkey', 'output_indicators', ['activity_id'])
    op.drop_column('output_indicators', 'district_name')
    op.drop_column('output_indicators', 'teenage_fathers')

    op.drop_column('activities', 'districts')
    op.drop_column('activities', 'focus_area_other')
