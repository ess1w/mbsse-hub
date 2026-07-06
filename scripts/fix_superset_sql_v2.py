#!/usr/bin/env python3
"""
Fix Superset dataset SQL and charts for MBSSE dashboard (Preset or self-hosted).

Fixes:
  - Partners by Organisation Type: stop summing pre-aggregated rows (659 CSOs bug)
  - KPI / filter datasets: district from oi.district_name → a.districts → o.districts
  - New: Activities by district (stacked by focus area)
  - New: Beneficiaries by district (stacked by gender)
  - New: Beneficiaries by vulnerability (pregnant girls, teenage mothers/fathers)

Usage (Preset):
  SUPERSET_URL='https://83f65675.us2a.app.preset.io' \\
  PRESET_API_TOKEN='...' PRESET_API_SECRET='...' \\
  SUPERSET_DB_ID=3 SUPERSET_DASHBOARD_ID=oBMOvaLJDme \\
  python3 fix_superset_sql_v2.py

Do not set SUPERSET_USER/PASSWORD on Preset — that login endpoint is disabled.
Auth uses manage.app.preset.io/api/v1 (Professional). api.app.preset.io is Enterprise-only.

Usage (local Docker):
  SUPERSET_URL=http://127.0.0.1:8088 SUPERSET_USER=admin SUPERSET_PASSWORD=admin \\
  python3 fix_superset_sql_v2.py

Run list_superset_databases.py first to discover SUPERSET_DB_ID and dashboard id.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import requests

from superset_auth import (
    login_session,
    mutating_request,
    normalize_workspace_url,
    resolve_dashboard_id,
    resolve_owner_id,
)
from superset_layout_utils import fix_layout_parents, link_chart_by_name

BASE = normalize_workspace_url(os.environ.get("SUPERSET_URL", "http://127.0.0.1:8088"))
DB_ID = int(os.environ.get("SUPERSET_DB_ID", "2"))
DASHBOARD_REF = os.environ.get(
    "SUPERSET_DASHBOARD_ID",
    os.environ.get("PRESET_DASHBOARD_ID", "10"),
)

ACTIVE_PERIOD = (
    "s.reporting_period_id = (SELECT id FROM reporting_periods "
    "WHERE is_active = true LIMIT 1)"
)

# Prefer per-district indicator rows, then activity districts, then org registry districts.
DISTRICT_ARR = """
CASE
  WHEN COALESCE(NULLIF(oi.district_name, ''), '') <> '' THEN ARRAY[oi.district_name]
  WHEN COALESCE(array_length(a.districts, 1), 0) > 0 THEN a.districts
  WHEN COALESCE(array_length(o.districts, 1), 0) > 0 THEN o.districts
  ELSE ARRAY['(unknown)']::varchar[]
END
"""

ACT_DISTRICT_ARR = """
CASE
  WHEN COALESCE(array_length(a.districts, 1), 0) > 0 THEN a.districts
  WHEN COALESCE(array_length(o.districts, 1), 0) > 0 THEN o.districts
  ELSE ARRAY['(unknown)']::varchar[]
END
"""

FOCUS_ARR = """
CASE
  WHEN COALESCE(array_length(a.focus_areas, 1), 0) > 0 THEN a.focus_areas
  ELSE ARRAY['(unknown)']::varchar[]
END
"""

ORG_DISTRICT_ARR = """
CASE
  WHEN COALESCE(array_length(o.districts, 1), 0) > 0 THEN o.districts
  ELSE ARRAY['(unknown)']::varchar[]
END
"""

ALLOC_TAIL = """
allocated AS (
  SELECT period, district, focus_area,
         (metric_value / n)::bigint
         + CASE WHEN rn <= (metric_value % n) THEN 1 ELSE 0 END AS metric_value
  FROM pairs
)
SELECT period, district, focus_area, SUM(metric_value) AS {col}
FROM allocated
GROUP BY 1, 2, 3
"""

ACTIVITY_PAIRS = f"""
WITH act AS (
  SELECT
    rp.label AS period,
    a.activity_id,
    {{metric_expr}} AS metric_value,
    {DISTRICT_ARR} AS district_arr,
    {FOCUS_ARR} AS focus_arr
  FROM output_indicators oi
  JOIN activities a ON a.activity_id = oi.activity_id
  JOIN submissions s ON s.id = a.submission_id
  JOIN reporting_periods rp ON rp.id = s.reporting_period_id
  JOIN organisations o ON o.org_id = s.org_id
  WHERE s.status IN ('submitted', 'verified')
    AND {{active_period}}
),
pairs AS (
  SELECT
    act.period,
    d.district,
    fa.focus_area,
    act.metric_value,
    ROW_NUMBER() OVER (
      PARTITION BY act.activity_id
      ORDER BY d.district, fa.focus_area
    ) AS rn,
    COUNT(*) OVER (PARTITION BY act.activity_id) AS n
  FROM act
  CROSS JOIN LATERAL unnest(act.district_arr) AS d(district)
  CROSS JOIN LATERAL unnest(act.focus_arr) AS fa(focus_area)
),
"""

SUBMISSION_PAIRS = f"""
WITH sub_focus AS (
  SELECT DISTINCT a.submission_id, fa.focus_area
  FROM activities a
  CROSS JOIN LATERAL unnest({FOCUS_ARR}) AS fa(focus_area)
),
sub AS (
  SELECT
    rp.label AS period,
    s.id AS submission_id,
    s.org_id,
    {{metric_expr}} AS metric_value,
    {ORG_DISTRICT_ARR} AS district_arr
  FROM submissions s
  JOIN reporting_periods rp ON rp.id = s.reporting_period_id
  JOIN organisations o ON o.org_id = s.org_id
  WHERE {{where_clause}}
    AND {{active_period}}
),
pairs AS (
  SELECT
    sub.period,
    d.district,
    sf.focus_area,
    sub.metric_value,
    ROW_NUMBER() OVER (
      PARTITION BY sub.submission_id
      ORDER BY d.district, sf.focus_area
    ) AS rn,
    COUNT(*) OVER (PARTITION BY sub.submission_id) AS n
  FROM sub
  JOIN sub_focus sf ON sf.submission_id = sub.submission_id
  CROSS JOIN LATERAL unnest(sub.district_arr) AS d(district)
),
"""

ORG_ONE_PAIRS = f"""
WITH sub_focus AS (
  SELECT DISTINCT a.submission_id, fa.focus_area
  FROM activities a
  CROSS JOIN LATERAL unnest({FOCUS_ARR}) AS fa(focus_area)
),
orgs AS (
  SELECT DISTINCT
    rp.label AS period,
    o.org_id,
    {ORG_DISTRICT_ARR} AS district_arr
  FROM organisations o
  JOIN submissions s ON s.org_id = o.org_id
  JOIN reporting_periods rp ON rp.id = s.reporting_period_id
  WHERE {{active_period}}
),
pairs AS (
  SELECT
    orgs.period,
    d.district,
    sf.focus_area,
    1 AS metric_value,
    ROW_NUMBER() OVER (
      PARTITION BY orgs.org_id
      ORDER BY d.district, sf.focus_area
    ) AS rn,
    COUNT(*) OVER (PARTITION BY orgs.org_id) AS n
  FROM orgs
  JOIN submissions s ON s.org_id = orgs.org_id AND {{active_period}}
  JOIN sub_focus sf ON sf.submission_id = s.id
  CROSS JOIN LATERAL unnest(orgs.district_arr) AS d(district)
  WHERE s.status IN ('submitted', 'verified')
),
"""

# Row-level org registry for correct COUNT(DISTINCT org_id) in charts.
PARTNERS_BY_ORG_TYPE = f"""
SELECT DISTINCT
  rp.label AS period,
  d.district,
  COALESCE(sf.focus_area, '(none)') AS focus_area,
  o.org_type,
  o.org_id
FROM organisations o
JOIN reporting_periods rp ON rp.is_active = true
CROSS JOIN LATERAL unnest({ORG_DISTRICT_ARR}) AS d(district)
LEFT JOIN submissions s
  ON s.org_id = o.org_id
 AND s.reporting_period_id = rp.id
LEFT JOIN activities a ON a.submission_id = s.id
LEFT JOIN LATERAL unnest({FOCUS_ARR}) AS sf(focus_area) ON a.activity_id IS NOT NULL
"""

ACTIVITIES_BY_DISTRICT = f"""
SELECT
  rp.label AS period,
  d.district,
  fa.focus_area,
  COUNT(DISTINCT a.activity_id) AS activity_count
FROM activities a
JOIN submissions s ON s.id = a.submission_id
JOIN reporting_periods rp ON rp.id = s.reporting_period_id
JOIN organisations o ON o.org_id = s.org_id
CROSS JOIN LATERAL unnest({ACT_DISTRICT_ARR}) AS d(district)
CROSS JOIN LATERAL unnest({FOCUS_ARR}) AS fa(focus_area)
WHERE s.status IN ('submitted', 'verified')
GROUP BY 1, 2, 3
"""

OBJECTIVE_LABELS = {
    "Obj 1": (
        "1. Promote Gender Equitable and Non-Violent Behaviours by Raising "
        "Awareness and Addressing Harmful Social Norms Perpetuating SRGBV"
    ),
    "Obj 2": (
        "2. Strengthen Institutional and Community Capacity to Prevent "
        "and Respond to SRGBV"
    ),
    "Obj 3": (
        "3. Ensure Sustained Commitment to SRGBV Prevention Through Policy "
        "Enforcement and Stakeholder Engagement"
    ),
}


def _objective_label_case(column: str = "objective_key") -> str:
    whens = "\n".join(
        f"      WHEN '{key}' THEN '{text.replace(chr(39), chr(39) + chr(39))}'"
        for key, text in OBJECTIVE_LABELS.items()
    )
    return f"    CASE {column}\n{whens}\n    END"


ACTIVITIES_BY_OBJECTIVE = f"""
SELECT
  {_objective_label_case("objective_key")} AS objective,
  COUNT(DISTINCT activity_id) AS activity_count
FROM (
  SELECT
    a.activity_id,
    CASE
      WHEN val IN ('obj1', 'Obj 1')
        OR val ~* '^obj\\s*1'
        OR val ~* '^1[.:]'
        THEN 'Obj 1'
      WHEN val IN ('obj2', 'Obj 2')
        OR val ~* '^obj\\s*2'
        OR val ~* '^2[.:]'
        THEN 'Obj 2'
      WHEN val IN ('obj3', 'Obj 3')
        OR val ~* '^obj\\s*3'
        OR val ~* '^3[.:]'
        THEN 'Obj 3'
    END AS objective_key
  FROM activities a
  JOIN submissions s ON s.id = a.submission_id
  CROSS JOIN LATERAL unnest(a.objectives) AS obj(val)
  WHERE s.status IN ('submitted', 'verified')
    AND {ACTIVE_PERIOD}
) mapped
WHERE objective_key IS NOT NULL
GROUP BY objective_key
ORDER BY objective_key
"""

SUBMISSION_STATUS_CURRENT_PERIOD = f"""
SELECT submission_status AS status, COUNT(*) AS submissions
FROM (
  SELECT
    o.org_id,
    CASE
      WHEN s.id IS NULL THEN 'Not submitted'
      WHEN s.status = 'draft' THEN 'Draft'
      WHEN s.status IN ('submitted', 'verified', 'flagged') THEN 'Submitted'
      ELSE INITCAP(s.status)
    END AS submission_status
  FROM organisations o
  LEFT JOIN submissions s
    ON s.org_id = o.org_id
   AND s.reporting_period_id = (
     SELECT id FROM reporting_periods WHERE is_active = true LIMIT 1
   )
  WHERE COALESCE(o.status, 'Active') != 'Inactive'
) partners
GROUP BY 1
ORDER BY 1
"""

VERIFICATION_STATUS_CURRENT_PERIOD = f"""
SELECT
  CASE s.status
    WHEN 'verified' THEN 'Verified'
    WHEN 'submitted' THEN 'Submitted (pending verification)'
    ELSE INITCAP(s.status)
  END AS status,
  COUNT(*) AS count
FROM submissions s
WHERE s.status IN ('submitted', 'verified')
  AND {ACTIVE_PERIOD}
GROUP BY 1
ORDER BY 1
"""

BENEFICIARIES_BY_DISTRICT_GENDER = f"""
WITH base AS (
  SELECT
    rp.label AS period,
    d.district,
    fa.focus_area,
    oi.students_inschool_f + oi.community_members_f AS female_ben,
    oi.students_inschool_m + oi.community_members_m AS male_ben
  FROM output_indicators oi
  JOIN activities a ON a.activity_id = oi.activity_id
  JOIN submissions s ON s.id = a.submission_id
  JOIN reporting_periods rp ON rp.id = s.reporting_period_id
  JOIN organisations o ON o.org_id = s.org_id
  CROSS JOIN LATERAL unnest({DISTRICT_ARR}) AS d(district)
  CROSS JOIN LATERAL unnest({FOCUS_ARR}) AS fa(focus_area)
  WHERE s.status IN ('submitted', 'verified')
)
SELECT period, district, focus_area, gender, SUM(beneficiaries) AS beneficiaries
FROM (
  SELECT period, district, focus_area, 'Female'::text AS gender, female_ben AS beneficiaries
  FROM base
  UNION ALL
  SELECT period, district, focus_area, 'Male'::text, male_ben
  FROM base
) u
GROUP BY 1, 2, 3, 4
"""

BENEFICIARIES_BY_VULNERABILITY = f"""
WITH base AS (
  SELECT
    rp.label AS period,
    d.district,
    fa.focus_area,
    COALESCE(oi.pregnant_girls, 0) AS pregnant_girls,
    COALESCE(oi.teenage_mothers, 0) AS teenage_mothers,
    COALESCE(oi.teenage_fathers, 0) AS teenage_fathers
  FROM output_indicators oi
  JOIN activities a ON a.activity_id = oi.activity_id
  JOIN submissions s ON s.id = a.submission_id
  JOIN reporting_periods rp ON rp.id = s.reporting_period_id
  JOIN organisations o ON o.org_id = s.org_id
  CROSS JOIN LATERAL unnest({DISTRICT_ARR}) AS d(district)
  CROSS JOIN LATERAL unnest({FOCUS_ARR}) AS fa(focus_area)
  WHERE s.status IN ('submitted', 'verified')
)
SELECT period, district, focus_area, vulnerability, SUM(beneficiaries) AS beneficiaries
FROM (
  SELECT period, district, focus_area, 'Pregnant girls'::text AS vulnerability, pregnant_girls AS beneficiaries
  FROM base
  UNION ALL
  SELECT period, district, focus_area, 'Teenage mothers', teenage_mothers
  FROM base
  UNION ALL
  SELECT period, district, focus_area, 'Teenage fathers', teenage_fathers
  FROM base
) u
GROUP BY 1, 2, 3, 4
"""

COMPLIANCE_DATASET = """
WITH active AS (
  SELECT id, label
  FROM reporting_periods
  WHERE is_active = true
  LIMIT 1
),
base AS (
  SELECT
    a.label AS period,
    d.district,
    COALESCE(sf.focus_area, '(none)') AS focus_area,
    o.org_id,
    MAX(CASE WHEN s.status IN ('submitted', 'verified') THEN 1 ELSE 0 END) AS is_compliant
  FROM organisations o
  CROSS JOIN active a
  CROSS JOIN LATERAL unnest(
    CASE
      WHEN COALESCE(array_length(o.districts, 1), 0) > 0 THEN o.districts
      ELSE ARRAY['(unknown)']::varchar[]
    END
  ) AS d(district)
  LEFT JOIN submissions s
    ON s.org_id = o.org_id
   AND s.reporting_period_id = a.id
  LEFT JOIN activities act ON act.submission_id = s.id
  LEFT JOIN LATERAL (
    SELECT DISTINCT unnest(
      CASE
        WHEN COALESCE(array_length(act.focus_areas, 1), 0) > 0 THEN act.focus_areas
        ELSE ARRAY['(none)']::varchar[]
      END
    ) AS focus_area
  ) sf ON true
  GROUP BY a.label, d.district, COALESCE(sf.focus_area, '(none)'), o.org_id
)
SELECT period, district, focus_area, org_id, is_compliant
FROM base
"""

DATASET_SQL_BY_NAME: dict[str, str] = {
    "Schools Reached": (
        ACTIVITY_PAIRS.format(
            metric_expr="(oi.schools_primary + oi.schools_jss + oi.schools_sss)",
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="schools_reached")
    ),
    "Reporting Partners": (
        ORG_ONE_PAIRS.format(active_period=ACTIVE_PERIOD) + ALLOC_TAIL.format(col="reporting_partners")
    ),
    "Beneficiaries This Period": (
        ACTIVITY_PAIRS.format(
            metric_expr=(
                "(oi.students_inschool_f + oi.students_inschool_m "
                "+ oi.community_members_f + oi.community_members_m)"
            ),
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="beneficiaries")
    ),
    "SRGBV Cases Reported": (
        SUBMISSION_PAIRS.format(
            metric_expr="COALESCE(s.cases_reported, 0)",
            where_clause="s.status IN ('submitted', 'verified')",
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="cases_reported")
    ),
    "SRGBV Cases Referred": (
        SUBMISSION_PAIRS.format(
            metric_expr="COALESCE(s.cases_referred, 0)",
            where_clause="s.status IN ('submitted', 'verified')",
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="cases_referred")
    ),
    "Schools with Functional SRGBV Mechanism": (
        ACTIVITY_PAIRS.format(
            metric_expr="""(
            SELECT v
            FROM unnest(ARRAY[
              oi.schools_with_focal_person,
              oi.schools_with_reporting_protocol,
              oi.schools_with_referral_pathway,
              oi.schools_held_schoolwide_campaign
            ]) AS v
            ORDER BY v DESC
            LIMIT 1 OFFSET 2
          )""",
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="schools_functional_mechanism")
    ),
    "Total Submissions": (
        SUBMISSION_PAIRS.format(
            metric_expr="1",
            where_clause="1=1",
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="total_submissions")
    ),
    "Reporting Compliance %": COMPLIANCE_DATASET,
    "Partners by Organisation Type": PARTNERS_BY_ORG_TYPE,
    "Partner Coverage by District": """
SELECT d.district_name AS district,
       COUNT(DISTINCT o.org_id) AS partner_count
FROM organisations o
JOIN districts d ON d.district_name = ANY(o.districts)
WHERE array_length(o.districts, 1) > 0
GROUP BY 1
ORDER BY 2 DESC""",
    "Activities by district": ACTIVITIES_BY_DISTRICT,
    "Activities by objective": ACTIVITIES_BY_OBJECTIVE,
    "Beneficiaries by district": BENEFICIARIES_BY_DISTRICT_GENDER,
    "Beneficiaries by vulnerability": BENEFICIARIES_BY_VULNERABILITY,
    "Submission Status — Current Period": SUBMISSION_STATUS_CURRENT_PERIOD,
    "Verification Status — Current Period": VERIFICATION_STATUS_CURRENT_PERIOD,
}

KPI_DATASET_IDS = {
    "Schools Reached": 44,
    "Reporting Partners": 45,
    "Beneficiaries This Period": 46,
    "SRGBV Cases Reported": 47,
    "SRGBV Cases Referred": 48,
    "Schools with Functional SRGBV Mechanism": 49,
    "Reporting Compliance %": 50,
    "Total Submissions": 55,
}

KPI_CHART_METRICS = {
    116: ("schools_reached", "SUM"),
    117: ("reporting_partners", "SUM"),
    118: ("beneficiaries", "SUM"),
    119: ("cases_reported", "SUM"),
    120: ("cases_referred", "SUM"),
    121: ("schools_functional_mechanism", "SUM"),
    123: ("total_submissions", "SUM"),
    122: (
        "compliance_pct",
        "SQL",
        (
            "ROUND(100.0 * COUNT(DISTINCT CASE WHEN is_compliant = 1 THEN org_id END) "
            "/ NULLIF(COUNT(DISTINCT org_id), 0), 1)"
        ),
    ),
}

PARTNERS_CHART_ID = 127

NEW_CHARTS = [
    {
        "name": "Activities by district",
        "dataset": "Activities by district",
        "viz_type": "echarts_timeseries_bar",
        "tab": "Activities",
        "width": 12,
        "height": 50,
        "params": {
            "x_axis": "district",
            "groupby": ["focus_area"],
            "metric_col": "activity_count",
            "stack": True,
        },
    },
    {
        "name": "Beneficiaries by district",
        "dataset": "Beneficiaries by district",
        "viz_type": "echarts_timeseries_bar",
        "tab": "Overview",
        "width": 12,
        "height": 50,
        "params": {
            "x_axis": "district",
            "groupby": ["gender"],
            "metric_col": "beneficiaries",
            "stack": True,
        },
    },
    {
        "name": "Beneficiaries by vulnerability",
        "dataset": "Beneficiaries by vulnerability",
        "viz_type": "echarts_timeseries_bar",
        "tab": "Beneficiaries",
        "width": 12,
        "height": 50,
        "params": {
            "x_axis": "vulnerability",
            "groupby": [],
            "metric_col": "beneficiaries",
            "stack": False,
        },
    },
]

# Preset may use alternate spellings from earlier imports
DATASET_NAME_ALIASES: dict[str, list[str]] = {
    "Submission Status — Current Period": ["Submission Status - Current Period"],
    "Verification Status — Current Period": ["Verification Status - Current Period"],
    "Activities by objective": ["Activities by Objective"],
}


class SupersetClient:
    def __init__(self, dashboard_id: int, owner_id: int) -> None:
        self.base = BASE
        self.dashboard_id = dashboard_id
        self.owner_id = owner_id
        self.session = login_session(BASE)

    def get_datasets(self) -> dict[str, int]:
        """Datasets on the configured database."""
        resp = self.session.get(
            f"{self.base}/api/v1/dataset/",
            params={
                "q": json.dumps(
                    {
                        "filters": [
                            {"col": "database", "opr": "rel_o_m", "value": [DB_ID]}
                        ],
                        "page_size": 500,
                    }
                )
            },
        )
        resp.raise_for_status()
        return {r["table_name"]: r["id"] for r in resp.json()["result"]}

    def get_all_datasets_by_name(self) -> dict[str, int]:
        """All virtual datasets in the workspace (any database)."""
        resp = self.session.get(
            f"{self.base}/api/v1/dataset/",
            params={"q": json.dumps({"page_size": 500})},
        )
        resp.raise_for_status()
        return {r["table_name"]: r["id"] for r in resp.json()["result"]}

    @staticmethod
    def _http_error(action: str, name: str, resp: requests.Response) -> None:
        body = resp.text[:800]
        raise RuntimeError(f"{action} dataset {name!r} failed ({resp.status_code}): {body}")

    def resolve_dataset_id(self, name: str, existing: dict[str, int]) -> int | None:
        if name in existing:
            return existing[name]
        all_by_name = self.get_all_datasets_by_name()
        if name in all_by_name:
            return all_by_name[name]
        for alt in DATASET_NAME_ALIASES.get(name, []):
            if alt in all_by_name:
                return all_by_name[alt]
        return None

    def upsert_dataset(self, name: str, sql: str, existing: dict[str, int]) -> int:
        sql = sql.strip()
        ds_id = self.resolve_dataset_id(name, existing)

        if ds_id is not None:
            resp = mutating_request(
                self.session,
                "PUT",
                f"{self.base}/api/v1/dataset/{ds_id}",
                json={"sql": sql, "table_name": name, "database_id": DB_ID},
            )
            if not resp.ok:
                self._http_error("Update", name, resp)
            return ds_id

        payload = {
            "database": DB_ID,
            "schema": "public",
            "table_name": name,
            "sql": sql,
            "owners": [self.owner_id],
        }
        resp = mutating_request(
            self.session,
            "POST",
            f"{self.base}/api/v1/dataset/",
            json=payload,
        )
        if not resp.ok:
            self._http_error("Create", name, resp)
        return resp.json()["id"]

    def refresh_metadata(self, ds_id: int) -> None:
        self.session.put(f"{self.base}/api/v1/dataset/{ds_id}/refresh").raise_for_status()

    def get_columns(self, ds_id: int) -> dict[str, dict]:
        resp = self.session.get(f"{self.base}/api/v1/dataset/{ds_id}")
        resp.raise_for_status()
        return {c["column_name"]: c for c in resp.json()["result"]["columns"]}

    def get_charts(self) -> dict[str, int]:
        resp = self.session.get(f"{self.base}/api/v1/chart/", params={"q": json.dumps({"page_size": 200})})
        resp.raise_for_status()
        return {r["slice_name"]: r["id"] for r in resp.json()["result"]}

    def metric(self, col: dict, agg: str = "SUM", label: str | None = None) -> dict:
        return {
            "expressionType": "SIMPLE",
            "column": {
                "column_name": col["column_name"],
                "type": col.get("type"),
                "type_generic": col.get("type_generic", 0),
            },
            "aggregate": agg,
            "label": label or f"{agg}({col['column_name']})",
            "optionName": f"metric_{uuid.uuid4().hex[:10]}",
        }

    def metric_distinct(self, col_name: str, label: str) -> dict:
        return {
            "expressionType": "SQL",
            "sqlExpression": f"COUNT(DISTINCT {col_name})",
            "label": label,
            "optionName": f"metric_{uuid.uuid4().hex[:10]}",
        }

    def upsert_chart(self, name: str, ds_id: int, viz_type: str, params: dict, existing: dict[str, int]) -> int:
        payload = {
            "slice_name": name,
            "viz_type": viz_type,
            "datasource_id": ds_id,
            "datasource_type": "table",
            "params": json.dumps(params),
            "owners": [self.owner_id],
        }
        if name in existing:
            chart_id = existing[name]
            mutating_request(
                self.session,
                "PUT",
                f"{self.base}/api/v1/chart/{chart_id}",
                json=payload,
            ).raise_for_status()
            return chart_id
        resp = mutating_request(
            self.session,
            "POST",
            f"{self.base}/api/v1/chart/",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def get_dashboard(self) -> dict:
        resp = self.session.get(f"{self.base}/api/v1/dashboard/{self.dashboard_id}")
        resp.raise_for_status()
        return resp.json()["result"]

    def save_dashboard(self, position: dict, json_metadata: dict) -> None:
        dash = self.get_dashboard()
        # positions inside json_metadata triggers dashboard_slices sync in Superset
        json_metadata = {**json_metadata, "positions": position}
        payload = {
            "dashboard_title": dash["dashboard_title"],
            "slug": dash.get("slug"),
            "owners": [self.owner_id],
            "position_json": json.dumps(position),
            "json_metadata": json.dumps(json_metadata),
        }
        mutating_request(
            self.session,
            "PUT",
            f"{self.base}/api/v1/dashboard/{self.dashboard_id}",
            json=payload,
        ).raise_for_status()

    def get_dashboard_charts(self) -> dict[str, int]:
        resp = self.session.get(
            f"{self.base}/api/v1/dashboard/{self.dashboard_id}/charts",
            params={"q": json.dumps({"page_size": 200})},
        )
        resp.raise_for_status()
        return {c["slice_name"]: c["id"] for c in resp.json()["result"]}

    def update_chart(self, chart_id: int, name: str, ds_id: int, viz_type: str, params: dict) -> int:
        payload = {
            "slice_name": name,
            "viz_type": viz_type,
            "datasource_id": ds_id,
            "datasource_type": "table",
            "params": json.dumps(params),
            "owners": [self.owner_id],
        }
        mutating_request(
            self.session,
            "PUT",
            f"{self.base}/api/v1/chart/{chart_id}",
            json=payload,
        ).raise_for_status()
        return chart_id


def bar_params(ds_id: int, spec: dict, metric: dict) -> dict:
    return {
        "datasource": f"{ds_id}__table",
        "viz_type": "echarts_timeseries_bar",
        "x_axis": spec["x_axis"],
        "metrics": [metric],
        "groupby": spec.get("groupby", []),
        "adhoc_filters": [],
        "row_limit": 10000,
        "truncate_metric": True,
        "show_empty_columns": True,
        "comparison_type": "values",
        "legendType": "scroll",
        "legendOrientation": "top",
        "show_legend": True,
        "rich_tooltip": True,
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
        "seriesType": "bar",
        "stack": spec.get("stack", False),
        "orientation": spec.get("orientation", "vertical"),
        "show_value": spec.get("show_value", False),
    }


def pie_params(ds_id: int, metric: dict) -> dict:
    return {
        "datasource": f"{ds_id}__table",
        "viz_type": "pie",
        "groupby": ["status"],
        "metric": metric,
        "adhoc_filters": [],
        "row_limit": 100,
        "sort_by_metric": True,
        "color_scheme": "supersetColors",
        "show_labels_threshold": 5,
        "show_legend": True,
        "legendType": "scroll",
        "legendOrientation": "top",
        "label_type": "key_percent",
        "number_format": "SMART_NUMBER",
        "show_labels": True,
        "labels_outside": True,
        "label_line": False,
        "donut": True,
        "outerRadius": 70,
        "innerRadius": 30,
    }


def find_chart_name(charts: dict[str, int], *candidates: str) -> str | None:
    for name in candidates:
        if name in charts:
            return name
    lower_map = {k.lower(): k for k in charts}
    for name in candidates:
        hit = lower_map.get(name.lower())
        if hit:
            return hit
    return None


def find_dashboard_chart(
    dashboard_charts: dict[str, int],
    *needles: str,
    exclude: tuple[str, ...] = (),
) -> tuple[str, int] | None:
    """Match a chart on the dashboard by name substring (case-insensitive)."""
    for name, chart_id in dashboard_charts.items():
        lower = name.lower()
        if exclude and any(ex in lower for ex in exclude):
            continue
        if any(n.lower() in lower for n in needles):
            return name, chart_id
    return None


def rewire_layout_chart_id(position: dict, chart_id: int, *slice_names: str) -> bool:
    names = {n.lower() for n in slice_names}
    for node in position.values():
        if not isinstance(node, dict) or node.get("type") != "CHART":
            continue
        slice_name = node.get("meta", {}).get("sliceName", "")
        if slice_name.lower() in names or any(n in slice_name.lower() for n in names):
            node["meta"]["chartId"] = chart_id
            node["id"] = f"CHART-{chart_id}"
            return True
    return False


def main() -> None:
    session = login_session(BASE)
    dashboard_id = resolve_dashboard_id(session, DASHBOARD_REF)
    owner_id = resolve_owner_id(session)
    print(f"workspace: {BASE}")
    print(f"dashboard: {DASHBOARD_REF} -> id {dashboard_id}")

    client = SupersetClient(dashboard_id, owner_id)
    print(f"database: SUPERSET_DB_ID={DB_ID}")
    if DB_ID == dashboard_id:
        raise SystemExit(
            "SUPERSET_DB_ID matches the dashboard id — these are different values.\n"
            "  SUPERSET_DB_ID=3      (from list_superset_databases.py)\n"
            "  SUPERSET_DASHBOARD_ID=oBMOvaLJDme  (or 9 — dashboard only)"
        )

    datasets = client.get_datasets()
    print(f"found {len(datasets)} existing datasets on database {DB_ID}")

    ds_ids: dict[str, int] = {}
    for name, sql in DATASET_SQL_BY_NAME.items():
        ds_ids[name] = client.upsert_dataset(name, sql, datasets)
        print(f"dataset: {name} -> {ds_ids[name]}")

    for name, ds_id in ds_ids.items():
        try:
            client.refresh_metadata(ds_id)
        except requests.HTTPError as exc:
            print(f"WARN metadata refresh failed for {name}: {exc}")

    # KPI datasets by fixed ID (local dashboard only — skipped on Preset)
    for name, ds_id in KPI_DATASET_IDS.items():
        if name in DATASET_SQL_BY_NAME:
            try:
                mutating_request(
                    client.session,
                    "PUT",
                    f"{client.base}/api/v1/dataset/{ds_id}",
                    json={"sql": DATASET_SQL_BY_NAME[name].strip(), "table_name": name},
                ).raise_for_status()
                client.refresh_metadata(ds_id)
                ds_ids[name] = ds_id
                print(f"kpi dataset id {ds_id}: {name}")
            except requests.HTTPError:
                pass

    charts = client.get_charts()
    dashboard_charts = client.get_dashboard_charts()

    # Fix Partners by Organisation Type — COUNT(DISTINCT org_id), not SUM(partners)
    partners_ds = ds_ids["Partners by Organisation Type"]
    partners_params = bar_params(
        partners_ds,
        {"x_axis": "org_type", "groupby": [], "stack": False},
        client.metric_distinct("org_id", "Partners"),
    )
    chart_id = charts.get("Partners by Organisation Type", PARTNERS_CHART_ID)
    client.upsert_chart(
        "Partners by Organisation Type",
        partners_ds,
        "echarts_timeseries_bar",
        partners_params,
        {**charts, "Partners by Organisation Type": chart_id},
    )
    print("fixed Partners by Organisation Type chart metric")

    # Submission status pie — org-level: Not submitted / Draft / Submitted
    sub_ds_name = "Submission Status — Current Period"
    if sub_ds_name in ds_ids:
        sub_ds = ds_ids[sub_ds_name]
        try:
            client.refresh_metadata(sub_ds)
        except requests.HTTPError:
            pass
        cols = client.get_columns(sub_ds)
        metric_col = cols.get("submissions") or cols.get("count")
        if metric_col:
            sub_match = find_dashboard_chart(
                dashboard_charts,
                "submission status",
                "submission status —",
                "submission status -",
                exclude=("verification",),
            )
            if sub_match:
                sub_chart_name, sub_chart_id = sub_match
                client.update_chart(
                    sub_chart_id,
                    sub_chart_name,
                    sub_ds,
                    "pie",
                    pie_params(sub_ds, client.metric(metric_col, "SUM")),
                )
                print(f"fixed {sub_chart_name} pie (Not submitted / Draft / Submitted)")
            else:
                sub_chart_name = find_chart_name(
                    charts,
                    "Submission Status — Current Period",
                    "Submission Status - Current Period",
                )
                if sub_chart_name:
                    client.upsert_chart(
                        sub_chart_name,
                        sub_ds,
                        "pie",
                        pie_params(sub_ds, client.metric(metric_col, "SUM")),
                        charts,
                    )
                    print(f"fixed {sub_chart_name} pie (Not submitted / Draft / Submitted)")

    # Verification status pie — submitted vs verified only (separate dataset)
    ver_ds_name = "Verification Status — Current Period"
    if ver_ds_name in ds_ids:
        ver_ds = ds_ids[ver_ds_name]
        try:
            client.refresh_metadata(ver_ds)
        except requests.HTTPError:
            pass
        cols = client.get_columns(ver_ds)
        metric_col = cols.get("count") or cols.get("submissions")
        if metric_col:
            ver_match = find_dashboard_chart(
                dashboard_charts,
                "verification status",
                "verification status —",
                "verification status -",
                exclude=("submission",),
            )
            if ver_match:
                ver_chart_name, ver_chart_id = ver_match
                client.update_chart(
                    ver_chart_id,
                    ver_chart_name,
                    ver_ds,
                    "pie",
                    pie_params(ver_ds, client.metric(metric_col, "SUM")),
                )
                print(f"fixed {ver_chart_name} pie (Submitted / Verified)")

    # Activities by objective — three bars with full objective text on axis + tooltip
    obj_ds_name = "Activities by objective"
    if obj_ds_name in ds_ids:
        obj_ds = ds_ids[obj_ds_name]
        try:
            client.refresh_metadata(obj_ds)
        except requests.HTTPError:
            pass
        cols = client.get_columns(obj_ds)
        if "activity_count" in cols:
            metric = client.metric(cols["activity_count"], "SUM")
            obj_params = bar_params(
                obj_ds,
                {
                    "x_axis": "objective",
                    "groupby": [],
                    "orientation": "horizontal",
                    "show_value": True,
                },
                metric,
            )
            obj_params["color_scheme"] = "colorsOfRainbow"
            obj_params["only_total"] = True
            obj_match = find_dashboard_chart(
                dashboard_charts, "activities by objective", "activities by objective"
            )
            if obj_match:
                obj_chart_name, obj_chart_id = obj_match
                client.update_chart(
                    obj_chart_id,
                    obj_chart_name,
                    obj_ds,
                    "echarts_timeseries_bar",
                    obj_params,
                )
                print(f"fixed {obj_chart_name} bar (full objective labels + tooltip)")
            else:
                obj_chart_name = find_chart_name(
                    charts,
                    "Activities by objective",
                    "Activities by Objective",
                )
                if obj_chart_name:
                    client.upsert_chart(
                        obj_chart_name,
                        obj_ds,
                        "echarts_timeseries_bar",
                        obj_params,
                        charts,
                    )
                    print(f"fixed {obj_chart_name} bar (full objective labels + tooltip)")

    # New / updated stacked charts
    for spec in NEW_CHARTS:
        ds_id = ds_ids[spec["dataset"]]
        cols = client.get_columns(ds_id)
        metric = client.metric(cols[spec["params"]["metric_col"]], "SUM")
        params = bar_params(ds_id, spec["params"], metric)
        cid = client.upsert_chart(spec["name"], ds_id, spec["viz_type"], params, charts)
        charts[spec["name"]] = cid
        print(f"chart: {spec['name']} -> {cid}")

    # Dashboard layout — append new charts to tabs if missing
    dash = client.get_dashboard()
    position = json.loads(dash["position_json"])
    json_metadata = json.loads(dash.get("json_metadata") or "{}")

    # Ensure dashboard tiles point at the charts we just updated
    sub_match = find_dashboard_chart(
        dashboard_charts, "submission status", exclude=("verification",)
    )
    if sub_match:
        rewire_layout_chart_id(position, sub_match[1], sub_match[0], "submission status")
    ver_match = find_dashboard_chart(
        dashboard_charts, "verification status", exclude=("submission",)
    )
    if ver_match:
        rewire_layout_chart_id(position, ver_match[1], ver_match[0], "verification status")
    obj_match = find_dashboard_chart(
        dashboard_charts, "activities by objective", "activities by objective"
    )
    if obj_match:
        rewire_layout_chart_id(position, obj_match[1], obj_match[0], "activities by objective")

    for spec in NEW_CHARTS:
        cid = charts[spec["name"]]
        comp_id = link_chart_by_name(
            position,
            spec["name"],
            cid,
            spec["tab"],
            spec["width"],
            spec["height"],
        )
        print(f"layout: {spec['name']} -> slice {cid} ({comp_id})")

    fix_layout_parents(position)
    client.save_dashboard(position, json_metadata)
    print(f"dashboard {dashboard_id} saved (charts linked via dashboard_slices)")


if __name__ == "__main__":
    main()
