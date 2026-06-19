#!/usr/bin/env python3
"""Rebuild KPI datasets with strict integer totals and correct compliance %."""

from __future__ import annotations

import json

from superset.app import create_app

ACTIVE_PERIOD = (
    "s.reporting_period_id = (SELECT id FROM reporting_periods WHERE is_active = true LIMIT 1)"
)

# Largest-remainder integer allocation across district x focus_area rows per entity.
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

ACTIVITY_PAIRS = """
WITH act AS (
  SELECT
    rp.label AS period,
    a.activity_id,
    {metric_expr} AS metric_value,
    o.districts,
    a.focus_areas
  FROM output_indicators oi
  JOIN activities a ON a.activity_id = oi.activity_id
  JOIN submissions s ON s.id = a.submission_id
  JOIN reporting_periods rp ON rp.id = s.reporting_period_id
  JOIN organisations o ON o.org_id = s.org_id
  WHERE s.status IN ('submitted', 'verified')
    AND {active_period}
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
  CROSS JOIN LATERAL unnest(
    CASE
      WHEN COALESCE(array_length(act.districts, 1), 0) > 0 THEN act.districts
      ELSE ARRAY['(unknown)']::varchar[]
    END
  ) AS d(district)
  CROSS JOIN LATERAL unnest(
    CASE
      WHEN COALESCE(array_length(act.focus_areas, 1), 0) > 0 THEN act.focus_areas
      ELSE ARRAY['(unknown)']::varchar[]
    END
  ) AS fa(focus_area)
),
"""

SUBMISSION_PAIRS = """
WITH sub_focus AS (
  SELECT DISTINCT a.submission_id, fa.focus_area
  FROM activities a
  CROSS JOIN LATERAL unnest(
    CASE
      WHEN COALESCE(array_length(a.focus_areas, 1), 0) > 0 THEN a.focus_areas
      ELSE ARRAY['(unknown)']::varchar[]
    END
  ) AS fa(focus_area)
),
sub AS (
  SELECT
    rp.label AS period,
    s.id AS submission_id,
    s.org_id,
    {metric_expr} AS metric_value,
    o.districts
  FROM submissions s
  JOIN reporting_periods rp ON rp.id = s.reporting_period_id
  JOIN organisations o ON o.org_id = s.org_id
  WHERE {where_clause}
    AND {active_period}
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
  CROSS JOIN LATERAL unnest(
    CASE
      WHEN COALESCE(array_length(sub.districts, 1), 0) > 0 THEN sub.districts
      ELSE ARRAY['(unknown)']::varchar[]
    END
  ) AS d(district)
),
"""

ORG_ONE_PAIRS = """
WITH sub_focus AS (
  SELECT DISTINCT a.submission_id, fa.focus_area
  FROM activities a
  CROSS JOIN LATERAL unnest(
    CASE
      WHEN COALESCE(array_length(a.focus_areas, 1), 0) > 0 THEN a.focus_areas
      ELSE ARRAY['(unknown)']::varchar[]
    END
  ) AS fa(focus_area)
),
orgs AS (
  SELECT DISTINCT
    rp.label AS period,
    o.org_id,
    o.districts
  FROM organisations o
  JOIN submissions s ON s.org_id = o.org_id
  JOIN reporting_periods rp ON rp.id = s.reporting_period_id
  WHERE {active_period}
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
  JOIN submissions s ON s.org_id = orgs.org_id AND {active_period}
  JOIN sub_focus sf ON sf.submission_id = s.id
  CROSS JOIN LATERAL unnest(
    CASE
      WHEN COALESCE(array_length(orgs.districts, 1), 0) > 0 THEN orgs.districts
      ELSE ARRAY['(unknown)']::varchar[]
    END
  ) AS d(district)
  WHERE s.status IN ('submitted', 'verified')
),
"""

DATASET_SQL = {
    44: (
        ACTIVITY_PAIRS.format(
            metric_expr="(oi.schools_primary + oi.schools_jss + oi.schools_sss)",
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="schools_reached")
    ),
    46: (
        ACTIVITY_PAIRS.format(
            metric_expr=(
                "(oi.students_inschool_f + oi.students_inschool_m "
                "+ oi.community_members_f + oi.community_members_m)"
            ),
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="beneficiaries")
    ),
    49: (
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
    47: (
        SUBMISSION_PAIRS.format(
            metric_expr="COALESCE(s.cases_reported, 0)",
            where_clause="s.status IN ('submitted', 'verified')",
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="cases_reported")
    ),
    48: (
        SUBMISSION_PAIRS.format(
            metric_expr="COALESCE(s.cases_referred, 0)",
            where_clause="s.status IN ('submitted', 'verified')",
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="cases_referred")
    ),
    55: (
        SUBMISSION_PAIRS.format(
            metric_expr="1",
            where_clause="1=1",
            active_period=ACTIVE_PERIOD,
        )
        + ALLOC_TAIL.format(col="total_submissions")
    ),
    45: ORG_ONE_PAIRS.format(active_period=ACTIVE_PERIOD) + ALLOC_TAIL.format(col="reporting_partners"),
    50: """
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
    MAX(
      CASE WHEN s.status IN ('submitted', 'verified') THEN 1 ELSE 0 END
    ) AS is_compliant
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
    SELECT DISTINCT unnest(act.focus_areas) AS focus_area
  ) sf ON true
  GROUP BY a.label, d.district, COALESCE(sf.focus_area, '(none)'), o.org_id
)
SELECT period, district, focus_area, org_id, is_compliant
FROM base
""",
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


def metric_simple(col: str, agg: str = "SUM") -> dict:
    return {
        "expressionType": "SIMPLE",
        "column": {"column_name": col},
        "aggregate": agg,
        "label": f"{agg}({col})" if agg != "COUNT" else "COUNT(*)",
        "optionName": f"metric_{col}",
    }


def metric_sql(sql: str, label: str) -> dict:
    return {
        "expressionType": "SQL",
        "sqlExpression": sql,
        "label": label,
        "optionName": f"metric_{label}",
    }


def main() -> None:
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.slice import Slice

        for ds_id, sql in DATASET_SQL.items():
            table = db.session.query(SqlaTable).filter_by(id=ds_id).one()
            table.sql = sql.strip()
        db.session.commit()

        for ds_id in DATASET_SQL:
            table = db.session.query(SqlaTable).filter_by(id=ds_id).one()
            table.fetch_metadata()
        db.session.commit()
        print("updated KPI datasets")

        for chart_id, spec in KPI_CHART_METRICS.items():
            chart = db.session.query(Slice).filter_by(id=chart_id).one()
            params = json.loads(chart.params)
            col, kind, *rest = spec
            if kind == "SQL":
                params["metric"] = metric_sql(rest[0], col)
            else:
                params["metric"] = metric_simple(col, kind)
            params["number_format"] = ",.0f" if chart_id != 122 else ",.1f"
            params["y_axis_format"] = ",.0f" if chart_id != 122 else ",.1f"
            chart.params = json.dumps(params)
        db.session.commit()
        print("updated KPI chart metrics")


if __name__ == "__main__":
    main()
