#!/usr/bin/env python3
"""Fix pie and beneficiaries chart rendering issues."""

from __future__ import annotations

import json
import uuid

import requests

BASE = "http://127.0.0.1:8088"


def metric(col_name: str, agg: str = "SUM") -> dict:
    return {
        "expressionType": "SIMPLE",
        "column": {"column_name": col_name},
        "aggregate": agg,
        "label": f"{agg}({col_name})",
        "optionName": f"metric_{uuid.uuid4().hex[:8]}",
    }


def main() -> None:
    s = requests.Session()
    token = s.post(
        f"{BASE}/api/v1/security/login",
        json={"username": "admin", "password": "admin", "provider": "db", "refresh": True},
    ).json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    csrf = s.get(f"{BASE}/api/v1/security/csrf_token/").json()["result"]
    s.headers["X-CSRFToken"] = csrf
    s.cookies.set("csrf_token", csrf)

    def get_chart(cid: int) -> dict:
        return s.get(f"{BASE}/api/v1/chart/{cid}").json()["result"]

    def save_chart(cid: int, params: dict) -> None:
        ch = get_chart(cid)
        payload = {
            "slice_name": ch["slice_name"],
            "viz_type": params["viz_type"],
            "datasource_id": ch["datasource_id"],
            "datasource_type": ch["datasource_type"],
            "params": json.dumps(params),
            "owners": [1],
        }
        r = s.put(f"{BASE}/api/v1/chart/{cid}", json=payload)
        r.raise_for_status()
        print(f"updated chart {cid}: {ch['slice_name']}")

    for cid, col in [(124, "submissions"), (125, "count")]:
        ch = get_chart(cid)
        old = json.loads(ch["params"])
        save_chart(
            cid,
            {
                "datasource": old["datasource"],
                "viz_type": "pie",
                "groupby": ["status"],
                "metric": metric(col),
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
                "adhoc_filters": [],
            },
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
        "only_total": False,
        "orientation": "vertical",
        "show_value": False,
    }

    for cid, x_axis, groupby_col in [
        (130, "period", "gender"),
        (131, "period", "beneficiary_type"),
        (132, "period", "age_group"),
        (133, "period", "gender"),
    ]:
        ch = get_chart(cid)
        old = json.loads(ch["params"])
        save_chart(
            cid,
            {
                **bar_defaults,
                "datasource": old["datasource"],
                "viz_type": "echarts_timeseries_bar",
                "x_axis": x_axis,
                "groupby": [groupby_col],
                "metrics": [metric("beneficiaries")],
            },
        )


if __name__ == "__main__":
    main()
