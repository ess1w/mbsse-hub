-- ============================================================
--  MBSSE School Safety Coordination Hub — PostgreSQL Schema
--  v1.0 — May 2026
-- ============================================================

-- Enable UUID generation (Postgres 13+ has gen_random_uuid() built-in)
-- CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- only needed on older PG

-- ============================================================
--  ENUMERATIONS
-- ============================================================

CREATE TYPE user_role        AS ENUM ('admin', 'viewer', 'partner');
CREATE TYPE org_type         AS ENUM ('INGO', 'Local NGO', 'UN Agency', 'Government', 'Academic', 'Other');
CREATE TYPE sla_status       AS ENUM ('Signed', 'Pending', 'Expired');
CREATE TYPE project_status   AS ENUM ('Active', 'Closed', 'Suspended');
CREATE TYPE objective_code   AS ENUM ('obj1', 'obj2', 'obj3');
CREATE TYPE submission_status AS ENUM ('draft', 'submitted', 'verified', 'flagged');
CREATE TYPE file_kind        AS ENUM ('photo', 'document');
CREATE TYPE reminder_type    AS ENUM ('deadline_approaching', 'overdue', 'manual');
CREATE TYPE reminder_status  AS ENUM ('pending', 'sent', 'failed');
CREATE TYPE budget_util      AS ENUM ('On track', 'Under-spending', 'Over-spending');
CREATE TYPE intervention_lvl AS ENUM ('School-based', 'Community', 'System-level');
CREATE TYPE impl_status      AS ENUM ('Completed', 'Ongoing', 'Delayed', 'Cancelled');
CREATE TYPE planned_actual   AS ENUM ('As planned', 'Modified');

-- ============================================================
--  REFERENCE — LOCATIONS (Sierra Leone admin hierarchy)
-- ============================================================

CREATE TABLE districts (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(60) UNIQUE NOT NULL,
    region      VARCHAR(30),            -- North, South, East, West
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE chiefdoms (
    id          SERIAL PRIMARY KEY,
    district_id INTEGER NOT NULL REFERENCES districts(id),
    name        VARCHAR(80) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (district_id, name)
);

CREATE TABLE schools (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    emis_code   VARCHAR(20) UNIQUE,
    name        VARCHAR(200) NOT NULL,
    school_type VARCHAR(40),            -- Primary, JSS, SSS, etc.
    chiefdom_id INTEGER REFERENCES chiefdoms(id),
    community   VARCHAR(120),
    gps_lat     NUMERIC(9, 6),
    gps_lng     NUMERIC(9, 6),
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
--  ORGANISATIONS  (Partner NGOs / UN Agencies / etc.)
-- ============================================================

CREATE TABLE organisations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(200) UNIQUE NOT NULL,
    acronym             VARCHAR(30),
    org_type            org_type NOT NULL,
    sla_status          sla_status NOT NULL DEFAULT 'Pending',
    sla_signed_date     DATE,
    sla_expiry_date     DATE,
    sla_document_url    TEXT,
    -- financials
    total_budget        NUMERIC(14, 2),
    budget_currency     VARCHAR(3) DEFAULT 'USD',
    funding_source      TEXT,
    gov_counterpart     TEXT,
    -- focal contact (primary)
    focal_name          VARCHAR(120),
    focal_email         VARCHAR(254),
    focal_phone         VARCHAR(30),
    -- programme dates
    project_period_start DATE,
    project_period_end   DATE,
    -- meta
    is_active           BOOLEAN NOT NULL DEFAULT true,
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

-- Organisations operate in many districts (many-to-many)
CREATE TABLE organisation_districts (
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    district_id     INTEGER NOT NULL REFERENCES districts(id),
    PRIMARY KEY (organisation_id, district_id)
);

-- ============================================================
--  USERS  (Authentication & authorisation)
-- ============================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(254) UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,          -- bcrypt hash
    full_name       VARCHAR(120) NOT NULL,
    role            user_role NOT NULL DEFAULT 'partner',
    -- partners are linked to exactly one organisation
    -- admin / viewer have NULL here
    organisation_id UUID REFERENCES organisations(id) ON DELETE SET NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    email_verified  BOOLEAN NOT NULL DEFAULT false,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Revoked / used tokens (for logout + password-reset single-use tokens)
CREATE TABLE token_blacklist (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jti         VARCHAR(64) UNIQUE NOT NULL,   -- JWT ID claim
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
--  PROJECTS  (one org can have many projects)
-- ============================================================

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    title           VARCHAR(300) NOT NULL,
    objective       objective_code NOT NULL,
    budget          NUMERIC(14, 2),
    budget_currency VARCHAR(3) DEFAULT 'USD',
    start_date      DATE,
    end_date        DATE,
    status          project_status NOT NULL DEFAULT 'Active',
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Projects operate in many districts
CREATE TABLE project_districts (
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    district_id INTEGER NOT NULL REFERENCES districts(id),
    PRIMARY KEY (project_id, district_id)
);

-- Projects span many focus areas (SRGBV, MHPSS, WASH, …)
CREATE TABLE project_focus_areas (
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    focus_area  VARCHAR(60) NOT NULL,
    PRIMARY KEY (project_id, focus_area)
);

-- ============================================================
--  REPORTING PERIODS  (bi-monthly cycles)
-- ============================================================

CREATE TABLE reporting_periods (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label       VARCHAR(40) NOT NULL,          -- e.g. "Mar–Apr 2026"
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    deadline    DATE NOT NULL,                 -- submission deadline
    is_active   BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_period UNIQUE (start_date, end_date)
);

-- ============================================================
--  SUBMISSIONS  (one per org × project × period)
-- ============================================================

CREATE TABLE submissions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organisation_id     UUID NOT NULL REFERENCES organisations(id),
    project_id          UUID NOT NULL REFERENCES projects(id),
    reporting_period_id UUID NOT NULL REFERENCES reporting_periods(id),
    submitted_by        UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_by         UUID REFERENCES users(id) ON DELETE SET NULL,
    status              submission_status NOT NULL DEFAULT 'draft',

    -- ── Section B: Geographic coverage ──────────────────────
    district_id         INTEGER REFERENCES districts(id),
    chiefdom_id         INTEGER REFERENCES chiefdoms(id),
    community           VARCHAR(120),
    school_id           UUID REFERENCES schools(id),

    -- ── Section C: Activity classification ──────────────────
    -- focus_areas stored in submission_focus_areas junction table
    objective           objective_code,
    tactic              VARCHAR(120),
    activity_type       VARCHAR(80),
    intervention_level  intervention_lvl,

    -- ── Section D: Implementation details ───────────────────
    activity_title      VARCHAR(300),
    impl_status         impl_status,
    description         TEXT,
    planned_vs_actual   planned_actual,
    activity_start      DATE,
    activity_end        DATE,

    -- ── Section E: Output indicators ────────────────────────
    schools_reached     INTEGER DEFAULT 0 CHECK (schools_reached >= 0),
    teachers_trained    INTEGER DEFAULT 0 CHECK (teachers_trained >= 0),
    students_reached    INTEGER DEFAULT 0 CHECK (students_reached >= 0),
    community_sessions  INTEGER DEFAULT 0 CHECK (community_sessions >= 0),
    safe_spaces_setup   INTEGER DEFAULT 0 CHECK (safe_spaces_setup >= 0),
    srgbv_referrals     INTEGER DEFAULT 0 CHECK (srgbv_referrals >= 0),
    -- disaggregation
    disagg_female       INTEGER DEFAULT 0 CHECK (disagg_female >= 0),
    disagg_male         INTEGER DEFAULT 0 CHECK (disagg_male >= 0),
    age_10_14           INTEGER DEFAULT 0 CHECK (age_10_14 >= 0),
    age_15_19           INTEGER DEFAULT 0 CHECK (age_15_19 >= 0),
    with_disability     INTEGER DEFAULT 0 CHECK (with_disability >= 0),
    out_of_school       INTEGER DEFAULT 0 CHECK (out_of_school >= 0),
    -- cross-field check: female + male <= students_reached (enforced in app layer)

    -- ── Section F: Outcome snapshot ─────────────────────────
    key_results         TEXT,
    observed_changes    TEXT,
    early_outcomes      TEXT,

    -- ── Section G: Financial tracking ───────────────────────
    expenditure         NUMERIC(14, 2) CHECK (expenditure >= 0),
    expenditure_currency VARCHAR(3) DEFAULT 'USD',
    budget_util         budget_util,

    -- ── Section H: Coordination ─────────────────────────────
    gov_engaged         BOOLEAN,
    gov_counterpart     TEXT,
    coordination_meetings INTEGER DEFAULT 0 CHECK (coordination_meetings >= 0),
    key_partners        TEXT,

    -- ── Section I: Challenges & risks ───────────────────────
    challenges          TEXT,
    risks               TEXT,
    mitigations         TEXT,

    -- ── Section J: Safeguarding ─────────────────────────────
    safeguarding_cases  BOOLEAN NOT NULL DEFAULT false,
    num_cases           INTEGER DEFAULT 0 CHECK (num_cases >= 0),
    referral_pathway    VARCHAR(120),
    safeguarding_action TEXT,

    -- ── Section L: Next period plan ─────────────────────────
    planned_activities  TEXT,
    support_needed      TEXT,

    -- ── Section M: Data quality (admin-managed) ─────────────
    review_flag         VARCHAR(40),   -- e.g. 'zero_beneficiaries', 'missing_data'
    review_notes        TEXT,

    -- ── Timestamps ──────────────────────────────────────────
    submitted_at        TIMESTAMPTZ,
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now(),

    -- One submission per org×project×period
    UNIQUE (organisation_id, project_id, reporting_period_id)
);

-- Focus areas selected for this submission (Section C multi-select)
CREATE TABLE submission_focus_areas (
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    focus_area    VARCHAR(60) NOT NULL,
    PRIMARY KEY (submission_id, focus_area)
);

-- ============================================================
--  UPLOADED FILES
-- ============================================================

CREATE TABLE uploaded_files (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id     UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    uploaded_by       UUID NOT NULL REFERENCES users(id),
    file_kind         file_kind NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_key        TEXT NOT NULL UNIQUE,    -- S3 key or local path UUID
    file_size_bytes   INTEGER NOT NULL CHECK (file_size_bytes > 0),
    mime_type         VARCHAR(100),
    storage_url       TEXT,                    -- presigned URL (refreshed on read)
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
--  REMINDERS  (automated + manual email log)
-- ============================================================

CREATE TABLE reminders (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporting_period_id UUID NOT NULL REFERENCES reporting_periods(id),
    organisation_id     UUID NOT NULL REFERENCES organisations(id),
    sent_to_email       VARCHAR(254) NOT NULL,
    reminder_type       reminder_type NOT NULL,
    status              reminder_status NOT NULL DEFAULT 'pending',
    error_message       TEXT,                  -- populated on failure
    scheduled_for       TIMESTAMPTZ,           -- when the scheduler queued it
    sent_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
--  AUDIT LOG  (immutable trail of every write action)
-- ============================================================

CREATE TABLE audit_logs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    action        VARCHAR(60) NOT NULL,        -- e.g. 'submission.submit', 'user.create'
    resource_type VARCHAR(60) NOT NULL,        -- e.g. 'submission', 'organisation'
    resource_id   UUID,
    diff          JSONB,                       -- {before: {…}, after: {…}}
    ip_address    INET,
    user_agent    TEXT,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
--  INDEXES  (performance for common query patterns)
-- ============================================================

-- Users
CREATE INDEX idx_users_email             ON users(email);
CREATE INDEX idx_users_organisation      ON users(organisation_id);

-- Submissions — the most-queried table
CREATE INDEX idx_submissions_org         ON submissions(organisation_id);
CREATE INDEX idx_submissions_period      ON submissions(reporting_period_id);
CREATE INDEX idx_submissions_status      ON submissions(status);
CREATE INDEX idx_submissions_org_period  ON submissions(organisation_id, reporting_period_id);

-- Files
CREATE INDEX idx_files_submission        ON uploaded_files(submission_id);

-- Reminders
CREATE INDEX idx_reminders_org_period    ON reminders(organisation_id, reporting_period_id);
CREATE INDEX idx_reminders_scheduled     ON reminders(scheduled_for) WHERE status = 'pending';

-- Audit
CREATE INDEX idx_audit_resource          ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_user              ON audit_logs(user_id);
CREATE INDEX idx_audit_created           ON audit_logs(created_at DESC);

-- ============================================================
--  SEED: Sierra Leone's 16 Districts
-- ============================================================

INSERT INTO districts (name, region) VALUES
  ('Bo',                'South'),
  ('Bombali',           'North'),
  ('Bonthe',            'South'),
  ('Falaba',            'North'),
  ('Kailahun',          'East'),
  ('Kambia',            'North'),
  ('Karene',            'North'),
  ('Kenema',            'East'),
  ('Koinadugu',         'North'),
  ('Kono',              'East'),
  ('Moyamba',           'South'),
  ('Port Loko',         'North'),
  ('Pujehun',           'South'),
  ('Tonkolili',         'North'),
  ('Western Area Rural','West'),
  ('Western Area Urban','West');

-- ============================================================
--  SEED: Active reporting period
-- ============================================================

INSERT INTO reporting_periods (label, start_date, end_date, deadline, is_active)
VALUES ('Mar–Apr 2026', '2026-03-01', '2026-04-30', '2026-06-30', true);
