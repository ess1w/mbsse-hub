#!/usr/bin/env python3
"""Build the MBSSE Superset dashboard to mirror Metabase."""

from __future__ import annotations

import json
import uuid
from typing import Any

import requests

BASE = "http://127.0.0.1:8088"
DB_ID = 2
DASHBOARD_ID = 10
OWNER_ID = 1

ACTIVE_PERIOD = (
    "s.reporting_period_id = (SELECT id FROM reporting_periods "
    "WHERE is_active = true LIMIT 1)"
)

BASE_FROM = """
FROM output_indicators oi
JOIN activities a ON a.activity_id = oi.activity_id
JOIN submissions s ON s.id = a.submission_id
JOIN reporting_periods rp ON rp.id = s.reporting_period_id
JOIN organisations o ON o.org_id = s.org_id
WHERE s.status IN ('submitted', 'verified')"""


def uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class SupersetClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        token = self.session.post(
            f"{BASE}/api/v1/security/login",
            json={
                "username": "admin",
                "password": "admin",
                "provider": "db",
                "refresh": True,
            },
        ).json()["access_token"]
        self.session.headers["Authorization"] = f"Bearer {token}"
        self.session.headers["Content-Type"] = "application/json"
        csrf = self.session.get(f"{BASE}/api/v1/security/csrf_token/").json()["result"]
        self.session.headers["X-CSRFToken"] = csrf
        self.session.cookies.set("csrf_token", csrf)

    def get_datasets(self) -> dict[str, int]:
        resp = self.session.get(
            f"{BASE}/api/v1/dataset/",
            params={"q": json.dumps({"filters": [{"col": "database", "opr": "rel_o_m", "value": [DB_ID]}]})},
        )
        resp.raise_for_status()
        return {r["table_name"]: r["id"] for r in resp.json()["result"]}

    def upsert_dataset(self, name: str, sql: str, existing: dict[str, int]) -> int:
        if name in existing:
            ds_id = existing[name]
            self.session.put(
                f"{BASE}/api/v1/dataset/{ds_id}",
                json={"sql": sql, "table_name": name},
            ).raise_for_status()
            return ds_id
        payload = {
            "database": DB_ID,
            "schema": "public",
            "table_name": name,
            "sql": sql,
            "owners": [OWNER_ID],
        }
        resp = self.session.post(f"{BASE}/api/v1/dataset/", json=payload)
        resp.raise_for_status()
        return resp.json()["id"]

    def get_columns(self, ds_id: int) -> dict[str, dict]:
        resp = self.session.get(f"{BASE}/api/v1/dataset/{ds_id}")
        resp.raise_for_status()
        return {c["column_name"]: c for c in resp.json()["result"]["columns"]}

    def upsert_chart(
        self,
        name: str,
        ds_id: int,
        viz_type: str,
        params: dict[str, Any],
        existing: dict[str, int],
    ) -> int:
        payload = {
            "slice_name": name,
            "viz_type": viz_type,
            "datasource_id": ds_id,
            "datasource_type": "table",
            "params": json.dumps(params),
            "owners": [OWNER_ID],
        }
        if name in existing:
            chart_id = existing[name]
            self.session.put(f"{BASE}/api/v1/chart/{chart_id}", json=payload).raise_for_status()
            return chart_id
        resp = self.session.post(f"{BASE}/api/v1/chart/", json=payload)
        resp.raise_for_status()
        return resp.json()["id"]

    def get_charts(self) -> dict[str, int]:
        resp = self.session.get(f"{BASE}/api/v1/chart/", params={"q": json.dumps({"page_size": 200})})
        resp.raise_for_status()
        result: dict[str, int] = {}
        for r in resp.json()["result"]:
            result[r["slice_name"]] = r["id"]
        return result

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

    def update_dashboard(self, chart_ids: dict[str, int], ds_ids: dict[str, int]) -> None:
        tabs_id = uid("TABS")
        tab_overview = uid("TAB")
        tab_beneficiaries = uid("TAB")
        tab_activities = uid("TAB")

        def row(parents: list[str], children: list[str]) -> tuple[str, dict]:
            row_id = uid("ROW")
            return row_id, {
                "id": row_id,
                "type": "ROW",
                "parents": parents,
                "children": children,
                "meta": {"background": "BACKGROUND_TRANSPARENT"},
            }

        def chart_component(chart_id: int, name: str, width: int, height: int) -> tuple[str, dict]:
            comp_id = f"CHART-{chart_id}"
            return comp_id, {
                "id": comp_id,
                "type": "CHART",
                "parents": [],
                "children": [],
                "meta": {
                    "chartId": chart_id,
                    "sliceName": name,
                    "uuid": str(uuid.uuid4()),
                    "width": width,
                    "height": height,
                },
            }

        position: dict[str, Any] = {
            "DASHBOARD_VERSION": "v2",
            "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
            "GRID_ID": {
                "type": "GRID",
                "id": "GRID_ID",
                "parents": ["ROOT_ID"],
                "children": [tabs_id],
            },
            "HEADER_ID": {
                "type": "HEADER",
                "id": "HEADER_ID",
                "meta": {"text": "MBSSE School Safety Hub"},
            },
            tabs_id: {
                "type": "TABS",
                "id": tabs_id,
                "parents": ["ROOT_ID", "GRID_ID"],
                "children": [tab_overview, tab_beneficiaries, tab_activities],
            },
            tab_overview: {
                "type": "TAB",
                "id": tab_overview,
                "parents": ["ROOT_ID", "GRID_ID", tabs_id],
                "children": [],
                "meta": {"text": "Overview", "defaultText": "Overview"},
            },
            tab_beneficiaries: {
                "type": "TAB",
                "id": tab_beneficiaries,
                "parents": ["ROOT_ID", "GRID_ID", tabs_id],
                "children": [],
                "meta": {"text": "Beneficiaries", "defaultText": "Beneficiaries"},
            },
            tab_activities: {
                "type": "TAB",
                "id": tab_activities,
                "parents": ["ROOT_ID", "GRID_ID", tabs_id],
                "children": [],
                "meta": {"text": "Activities", "defaultText": "Activities"},
            },
        }

        def add_tab_charts(tab_id: str, specs: list[tuple[str, int, int]]) -> None:
            tab_parents = ["ROOT_ID", "GRID_ID", tabs_id, tab_id]
            row_specs: list[list[tuple[str, int, int]]] = []
            current: list[tuple[str, int, int]] = []
            used = 0
            for name, width, height in specs:
                if used + width > 12:
                    row_specs.append(current)
                    current = []
                    used = 0
                current.append((name, width, height))
                used += width
            if current:
                row_specs.append(current)

            for row_spec in row_specs:
                chart_entries = []
                row_children = []
                for name, width, height in row_spec:
                    cid = chart_ids[name]
                    comp_id, comp = chart_component(cid, name, width, height)
                    chart_entries.append((comp_id, comp, width, height))
                    row_children.append(comp_id)

                row_id, row_obj = row(tab_parents, row_children)
                position[row_id] = row_obj
                position[tab_id]["children"].append(row_id)

                for comp_id, comp, _, _ in chart_entries:
                    comp["parents"] = tab_parents + [row_id]
                    position[comp_id] = comp

        add_tab_charts(
            tab_overview,
            [
                ("Schools Reached", 3, 20),
                ("Reporting Partners", 3, 20),
                ("Beneficiaries This Period", 3, 20),
                ("Reporting Compliance %", 3, 20),
                ("SRGBV Cases Reported", 3, 20),
                ("SRGBV Cases Referred", 3, 20),
                ("Schools with Functional SRGBV Mechanism", 3, 20),
                ("Total Submissions", 3, 20),
                ("Submission Status — Current Period", 4, 45),
                ("Verification Status — Current Period", 4, 45),
                ("Beneficiaries by sex", 4, 45),
                ("Partners by Organisation Type", 4, 45),
                ("Partner Coverage by District", 12, 60),
            ],
        )
        add_tab_charts(
            tab_beneficiaries,
            [
                ("Beneficiaries over time", 12, 50),
                ("Beneficiaries by type over time", 12, 50),
                ("Beneficiaries by age group over time", 12, 50),
                ("Beneficiaries with disabilities over time", 12, 50),
            ],
        )
        add_tab_charts(
            tab_activities,
            [
                ("Activities by Focus Area", 6, 50),
                ("Activities by objective", 6, 50),
            ],
        )

        all_chart_ids = list(chart_ids.values())
        native_filters = [
            {
                "id": uid("NATIVE_FILTER"),
                "name": "District",
                "filterType": "filter_select",
                "targets": [{"datasetId": ds_ids["Filter Districts"], "column": {"name": "district"}}],
                "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}},
                "controlValues": {
                    "enableEmptyFilter": False,
                    "defaultToFirstItem": False,
                    "multiSelect": True,
                    "searchAllOptions": False,
                    "inverseSelection": False,
                },
                "cascadeParentIds": [],
                "scope": {
                    "rootPath": ["ROOT_ID"],
                    "excluded": [
                        chart_ids.get("Beneficiaries over time"),
                        chart_ids.get("Beneficiaries by type over time"),
                        chart_ids.get("Beneficiaries by age group over time"),
                        chart_ids.get("Beneficiaries with disabilities over time"),
                    ],
                },
                "type": "NATIVE_FILTER",
                "description": "",
                "chartsInScope": [c for c in all_chart_ids if c],
                "tabsInScope": [tab_overview, tab_beneficiaries, tab_activities],
            },
            {
                "id": uid("NATIVE_FILTER"),
                "name": "Focus area",
                "filterType": "filter_select",
                "targets": [{"datasetId": ds_ids["Filter Focus Areas"], "column": {"name": "focus_area"}}],
                "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}},
                "controlValues": {
                    "enableEmptyFilter": False,
                    "defaultToFirstItem": False,
                    "multiSelect": True,
                    "searchAllOptions": False,
                    "inverseSelection": False,
                },
                "cascadeParentIds": [],
                "scope": {
                    "rootPath": ["ROOT_ID"],
                    "excluded": [
                        chart_ids.get("Beneficiaries over time"),
                        chart_ids.get("Beneficiaries by type over time"),
                        chart_ids.get("Beneficiaries by age group over time"),
                        chart_ids.get("Beneficiaries with disabilities over time"),
                    ],
                },
                "type": "NATIVE_FILTER",
                "description": "",
                "chartsInScope": [c for c in all_chart_ids if c],
                "tabsInScope": [tab_overview, tab_beneficiaries, tab_activities],
            },
            {
                "id": uid("NATIVE_FILTER"),
                "name": "Reporting Period",
                "filterType": "filter_select",
                "targets": [{"datasetId": 24, "column": {"name": "label"}}],
                "defaultDataMask": {
                    "extraFormData": {
                        "filters": [{"col": "label", "op": "IN", "val": ["Jan–Feb 2026"]}]
                    },
                    "filterState": {"value": ["Jan–Feb 2026"], "label": "Jan–Feb 2026"},
                    "ownState": {},
                },
                "controlValues": {
                    "enableEmptyFilter": False,
                    "defaultToFirstItem": False,
                    "multiSelect": False,
                    "searchAllOptions": False,
                    "inverseSelection": False,
                },
                "cascadeParentIds": [],
                "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
                "type": "NATIVE_FILTER",
                "description": "",
                "chartsInScope": all_chart_ids,
                "tabsInScope": [tab_overview, tab_beneficiaries, tab_activities],
            },
        ]

        payload = {
            "dashboard_title": "MBSSE School Safety Hub",
            "slug": "mbsse-school-safety-hub",
            "owners": [OWNER_ID],
            "position_json": json.dumps(position),
            "json_metadata": json.dumps(
                {
                    "timed_refresh_immune_slices": [],
                    "expanded_slices": {},
                    "refresh_frequency": 0,
                    "color_scheme": "",
                    "label_colors": {},
                    "cross_filters_enabled": True,
                    "default_filters": "{}",
                    "chart_configuration": {},
                    "native_filter_configuration": native_filters,
                    "shared_label_colors": [],
                    "color_scheme_domain": [],
                    "map_label_colors": {},
                }
            ),
        }
        self.session.put(f"{BASE}/api/v1/dashboard/{DASHBOARD_ID}", json=payload).raise_for_status()


def build_sql_queries() -> dict[str, str]:
    return {
        "Filter Districts": "SELECT district_name AS district FROM districts ORDER BY 1",
        "Filter Focus Areas": """
SELECT DISTINCT UNNEST(focus_areas) AS focus_area
FROM activities
WHERE array_length(focus_areas, 1) > 0
ORDER BY 1""",
        "Schools Reached": f"""
SELECT SUM(oi.schools_primary + oi.schools_jss + oi.schools_sss) AS schools_reached
{BASE_FROM}
  AND {ACTIVE_PERIOD}""",
        "Reporting Partners": f"""
SELECT COUNT(DISTINCT s.org_id) AS reporting_partners
FROM submissions s
JOIN organisations o ON o.org_id = s.org_id
WHERE s.status IN ('submitted', 'verified')
  AND {ACTIVE_PERIOD}""",
        "Beneficiaries This Period": f"""
SELECT SUM(oi.students_inschool_f + oi.students_inschool_m
         + oi.community_members_f + oi.community_members_m) AS beneficiaries
{BASE_FROM}
  AND {ACTIVE_PERIOD}""",
        "SRGBV Cases Reported": f"""
SELECT SUM(s.cases_reported) AS cases_reported
FROM submissions s
WHERE s.status IN ('submitted', 'verified')
  AND {ACTIVE_PERIOD}""",
        "SRGBV Cases Referred": f"""
SELECT SUM(s.cases_referred) AS cases_referred
FROM submissions s
WHERE s.status IN ('submitted', 'verified')
  AND {ACTIVE_PERIOD}""",
        "Schools with Functional SRGBV Mechanism": f"""
SELECT SUM(third_highest) AS schools_functional_mechanism
FROM (
  SELECT (
    SELECT v
    FROM unnest(ARRAY[
      oi.schools_with_focal_person,
      oi.schools_with_reporting_protocol,
      oi.schools_with_referral_pathway,
      oi.schools_held_schoolwide_campaign
    ]) AS v
    ORDER BY v DESC
    LIMIT 1 OFFSET 2
  ) AS third_highest
  {BASE_FROM}
    AND {ACTIVE_PERIOD}
) x""",
        "Reporting Compliance %": """
SELECT ROUND(
    100.0 * SUM(CASE WHEN s.status IN ('submitted','verified') THEN 1 ELSE 0 END)
          / COUNT(DISTINCT o.org_id), 1) AS compliance_pct
FROM organisations o
LEFT JOIN submissions s ON s.org_id = o.org_id
  AND s.reporting_period_id = (SELECT id FROM reporting_periods WHERE is_active = true LIMIT 1)""",
        "Beneficiaries by sex": f"""
SELECT 'Female' AS sex,
       SUM(oi.students_inschool_f + oi.community_members_f) AS beneficiaries
{BASE_FROM}
UNION ALL
SELECT 'Male',
       SUM(oi.students_inschool_m + oi.community_members_m)
{BASE_FROM}""",
        "Partners by Organisation Type": f"""
SELECT DISTINCT
  rp.label AS period,
  d.district,
  COALESCE(sf.focus_area, '(none)') AS focus_area,
  o.org_type,
  o.org_id
FROM organisations o
JOIN reporting_periods rp ON rp.is_active = true
CROSS JOIN LATERAL unnest(
  CASE
    WHEN COALESCE(array_length(o.districts, 1), 0) > 0 THEN o.districts
    ELSE ARRAY['(unknown)']::varchar[]
  END
) AS d(district)
LEFT JOIN submissions s
  ON s.org_id = o.org_id AND s.reporting_period_id = rp.id
LEFT JOIN activities a ON a.submission_id = s.id
LEFT JOIN LATERAL unnest(
  CASE
    WHEN COALESCE(array_length(a.focus_areas, 1), 0) > 0 THEN a.focus_areas
    ELSE ARRAY['(none)']::varchar[]
  END
) AS sf(focus_area) ON a.activity_id IS NOT NULL""",
        "Partner Coverage by District": """
SELECT d.district_name AS district,
       COUNT(DISTINCT o.org_id) AS partner_count
FROM organisations o
JOIN districts d ON d.district_name = ANY(o.districts)
WHERE array_length(o.districts, 1) > 0
GROUP BY 1
ORDER BY 2 DESC""",
        "Submission Status — Current Period": f"""
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
ORDER BY 1""",
        "Verification Status — Current Period": f"""
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
ORDER BY 1""",
        "Total Submissions": f"""
SELECT COUNT(*) AS total_submissions
FROM submissions s
WHERE {ACTIVE_PERIOD}""",
        "Activities by Focus Area": f"""
SELECT fa AS focus_area,
       COUNT(DISTINCT a.submission_id) AS submissions
FROM activities a
JOIN submissions s ON s.id = a.submission_id
CROSS JOIN LATERAL unnest(a.focus_areas) AS fa
WHERE s.status IN ('submitted', 'verified')
  AND {ACTIVE_PERIOD}
GROUP BY 1
ORDER BY 2 DESC""",
        "Activities by objective": f"""
SELECT
  CASE objective_key
    WHEN 'Obj 1' THEN '1. Promote Gender Equitable and Non-Violent Behaviours by Raising Awareness and Addressing Harmful Social Norms Perpetuating SRGBV'
    WHEN 'Obj 2' THEN '2. Strengthen Institutional and Community Capacity to Prevent and Respond to SRGBV'
    WHEN 'Obj 3' THEN '3. Ensure Sustained Commitment to SRGBV Prevention Through Policy Enforcement and Stakeholder Engagement'
  END AS objective,
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
ORDER BY objective_key""",
        "Beneficiaries over time": f"""
SELECT rp.label AS period, 'Female' AS gender,
       SUM(oi.students_inschool_f + oi.community_members_f) AS beneficiaries
{BASE_FROM}
GROUP BY 1, 2
UNION ALL
SELECT rp.label, 'Male',
       SUM(oi.students_inschool_m + oi.community_members_m)
{BASE_FROM}
GROUP BY 1, 2
ORDER BY 1, 2""",
        "Beneficiaries by type over time": f"""
SELECT rp.label AS period, 'In-school students' AS beneficiary_type,
       SUM(oi.students_inschool_f + oi.students_inschool_m) AS beneficiaries
{BASE_FROM}
GROUP BY 1, 2
UNION ALL
SELECT rp.label, 'Teachers', SUM(oi.teachers_f + oi.teachers_m)
{BASE_FROM}
GROUP BY 1, 2
UNION ALL
SELECT rp.label, 'Community members',
       SUM(oi.community_members_f + oi.community_members_m)
{BASE_FROM}
GROUP BY 1, 2
ORDER BY 1, 2""",
        "Beneficiaries by age group over time": f"""
SELECT rp.label AS period, 'Age 10–14' AS age_group,
       SUM(oi.students_inschool_age_10_14) AS beneficiaries
{BASE_FROM}
GROUP BY 1, 2
UNION ALL
SELECT rp.label, 'Age 15–19', SUM(oi.students_inschool_age_15_19)
{BASE_FROM}
GROUP BY 1, 2
UNION ALL
SELECT rp.label, 'Other / unknown',
       SUM((oi.students_inschool_f + oi.students_inschool_m)
           - COALESCE(oi.students_inschool_age_10_14, 0)
           - COALESCE(oi.students_inschool_age_15_19, 0))
{BASE_FROM}
GROUP BY 1, 2
ORDER BY 1, 2""",
        "Beneficiaries with disabilities over time": f"""
SELECT rp.label AS period, 'Female' AS gender,
       SUM(oi.students_disability_f) AS beneficiaries
{BASE_FROM}
GROUP BY 1, 2
UNION ALL
SELECT rp.label, 'Male', SUM(oi.students_disability_m)
{BASE_FROM}
GROUP BY 1, 2
ORDER BY 1, 2""",
    }


def main() -> None:
    client = SupersetClient()
    sql_queries = build_sql_queries()
    datasets = client.get_datasets()

    ds_ids: dict[str, int] = {}
    for name, sql in sql_queries.items():
        ds_ids[name] = client.upsert_dataset(name, sql.strip(), datasets)
        print(f"dataset: {name} -> {ds_ids[name]}")

    charts = client.get_charts()
    chart_ids: dict[str, int] = {}

    def ds(name: str) -> int:
        return ds_ids[name]

    def cols(name: str) -> dict[str, dict]:
        return client.get_columns(ds(name))

    for title, col_name, agg in [
        ("Schools Reached", "schools_reached", "SUM"),
        ("Reporting Partners", "reporting_partners", "SUM"),
        ("Beneficiaries This Period", "beneficiaries", "SUM"),
        ("SRGBV Cases Reported", "cases_reported", "SUM"),
        ("SRGBV Cases Referred", "cases_referred", "SUM"),
        ("Schools with Functional SRGBV Mechanism", "schools_functional_mechanism", "SUM"),
        ("Reporting Compliance %", "compliance_pct", "SUM"),
        ("Total Submissions", "total_submissions", "SUM"),
    ]:
        c = cols(title)[col_name]
        chart_ids[title] = client.upsert_chart(
            title,
            ds(title),
            "big_number_total",
            {
                "datasource": f"{ds(title)}__table",
                "viz_type": "big_number_total",
                "metric": client.metric(c, agg),
                "adhoc_filters": [],
            },
            charts,
        )

    for title in ["Submission Status — Current Period", "Verification Status — Current Period"]:
        c = cols(title)
        metric_col = c["submissions"] if "submissions" in c else c["count"]
        chart_ids[title] = client.upsert_chart(
            title,
            ds(title),
            "pie",
            {
                "datasource": f"{ds(title)}__table",
                "viz_type": "pie",
                "groupby": ["status"],
                "metric": client.metric(metric_col, "SUM"),
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
            },
            charts,
        )

    c = cols("Beneficiaries by sex")
    chart_ids["Beneficiaries by sex"] = client.upsert_chart(
        "Beneficiaries by sex",
        ds("Beneficiaries by sex"),
        "echarts_timeseries_bar",
        {
            "datasource": f"{ds('Beneficiaries by sex')}__table",
            "viz_type": "echarts_timeseries_bar",
            "x_axis": "sex",
            "metrics": [client.metric(c["beneficiaries"], "SUM")],
            "groupby": [],
            "adhoc_filters": [],
            "row_limit": 10000,
        },
        charts,
    )

    c = cols("Partners by Organisation Type")
    chart_ids["Partners by Organisation Type"] = client.upsert_chart(
        "Partners by Organisation Type",
        ds("Partners by Organisation Type"),
        "echarts_timeseries_bar",
        {
            "datasource": f"{ds('Partners by Organisation Type')}__table",
            "viz_type": "echarts_timeseries_bar",
            "x_axis": "org_type",
            "metrics": [{
                "expressionType": "SQL",
                "sqlExpression": "COUNT(DISTINCT org_id)",
                "label": "Partners",
                "optionName": f"metric_{uuid.uuid4().hex[:10]}",
            }],
            "groupby": [],
            "adhoc_filters": [],
            "row_limit": 10000,
        },
        charts,
    )

    c = cols("Partner Coverage by District")
    chart_ids["Partner Coverage by District"] = client.upsert_chart(
        "Partner Coverage by District",
        ds("Partner Coverage by District"),
        "country_map",
        {
            "datasource": f"{ds('Partner Coverage by District')}__table",
            "viz_type": "country_map",
            "select_country": "sierra_leone_districts",
            "entity": "district",
            "metric": client.metric(c["partner_count"], "SUM"),
            "linear_color_scheme": "superset_seq_1",
            "number_format": "SMART_NUMBER",
        },
        charts,
    )

    for title, x_axis, metric_name in [
        ("Activities by Focus Area", "focus_area", "submissions"),
        ("Activities by objective", "objective", "activity_count"),
    ]:
        c = cols(title)
        bar_spec = {
            "datasource": f"{ds(title)}__table",
            "viz_type": "echarts_timeseries_bar",
            "x_axis": x_axis,
            "metrics": [client.metric(c[metric_name], "SUM")],
            "groupby": [],
            "adhoc_filters": [],
            "row_limit": 10000,
        }
        if title == "Activities by objective":
            bar_spec["orientation"] = "horizontal"
            bar_spec["show_value"] = True
        chart_ids[title] = client.upsert_chart(
            title,
            ds(title),
            "echarts_timeseries_bar",
            bar_spec,
            charts,
        )

    bar_defaults = {
        "adhoc_filters": [],
        "row_limit": 10000,
        "truncate_metric": True,
        "show_empty_columns": True,
        "comparison_type": "values",
        "annotation_layers": [],
        "forecastEnabled": False,
        "legendType": "scroll",
        "legendOrientation": "top",
        "show_legend": True,
        "rich_tooltip": True,
        "tooltipTimeFormat": "smart_date",
        "x_axis_time_format": "smart_date",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
        "seriesType": "bar",
        "stack": False,
        "orientation": "vertical",
        "show_value": False,
    }

    for title, x_axis, series_col in [
        ("Beneficiaries over time", "period", "gender"),
        ("Beneficiaries by type over time", "period", "beneficiary_type"),
        ("Beneficiaries by age group over time", "period", "age_group"),
        ("Beneficiaries with disabilities over time", "period", "gender"),
    ]:
        c = cols(title)
        chart_ids[title] = client.upsert_chart(
            title,
            ds(title),
            "echarts_timeseries_bar",
            {
                **bar_defaults,
                "datasource": f"{ds(title)}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": x_axis,
                "metrics": [client.metric(c["beneficiaries"], "SUM")],
                "groupby": [series_col],
            },
            charts,
        )

    client.update_dashboard(chart_ids, ds_ids)
    print("Dashboard updated:", DASHBOARD_ID)
    print(json.dumps(chart_ids, indent=2))


if __name__ == "__main__":
    main()
