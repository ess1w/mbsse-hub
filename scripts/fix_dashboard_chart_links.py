#!/usr/bin/env python3
"""
Link new dashboard charts to the dashboard (fixes MissingChart placeholders).

Run on Preset after charts exist but show:
  "There is no chart definition associated with this component..."

The dashboard layout often references local chart ids (e.g. 134) that do not
exist on Preset. This script remaps them to the real slice ids by name and
syncs dashboard_slices via json_metadata.positions.

Usage (Preset):
  SUPERSET_URL='https://83f65675.us2a.app.preset.io' \\
  PRESET_API_TOKEN='...' PRESET_API_SECRET='...' \\
  SUPERSET_DASHBOARD_ID=oBMOvaLJDme python3 fix_dashboard_chart_links.py
"""

from __future__ import annotations

import json
import os
import sys

import requests

from superset_auth import (
    login_session,
    mutating_request,
    normalize_workspace_url,
    resolve_dashboard_id,
    resolve_owner_id,
)
from superset_layout_utils import (
    fix_layout_parents,
    link_chart_by_name,
    remove_stale_chart_components,
)

BASE = normalize_workspace_url(os.environ.get("SUPERSET_URL", "http://127.0.0.1:8088"))
DASHBOARD_REF = os.environ.get(
    "SUPERSET_DASHBOARD_ID",
    os.environ.get("PRESET_DASHBOARD_ID", "10"),
)

CHART_SPECS = [
    {
        "name": "Activities by district",
        "tab": "Activities",
        "width": 12,
        "height": 50,
    },
    {
        "name": "Beneficiaries by district",
        "tab": "Overview",
        "width": 12,
        "height": 50,
    },
    {
        "name": "Beneficiaries by vulnerability",
        "tab": "Beneficiaries",
        "width": 12,
        "height": 50,
    },
]


def get_charts(s: requests.Session, base: str) -> dict[str, int]:
    r = s.get(f"{base}/api/v1/chart/", params={"q": json.dumps({"page_size": 200})})
    r.raise_for_status()
    return {c["slice_name"]: c["id"] for c in r.json()["result"]}


def get_dashboard(s: requests.Session, base: str, dashboard_id: int) -> dict:
    r = s.get(f"{base}/api/v1/dashboard/{dashboard_id}")
    r.raise_for_status()
    return r.json()["result"]


def get_linked_chart_ids(s: requests.Session, base: str, dashboard_id: int) -> set[int]:
    r = s.get(
        f"{base}/api/v1/dashboard/{dashboard_id}/charts",
        params={"q": json.dumps({"page_size": 200})},
    )
    r.raise_for_status()
    return {c["id"] for c in r.json()["result"]}


def main() -> None:
    s = login_session(BASE)
    dashboard_id = resolve_dashboard_id(s, DASHBOARD_REF)
    owner_id = resolve_owner_id(s)
    charts = get_charts(s, BASE)
    names = {spec["name"] for spec in CHART_SPECS}
    missing = [spec["name"] for spec in CHART_SPECS if spec["name"] not in charts]
    if missing:
        raise SystemExit(
            f"Charts not found — run fix_superset_sql_v2.py first to create them: {missing}"
        )

    dash = get_dashboard(s, BASE, dashboard_id)
    position = json.loads(dash["position_json"])
    json_metadata = json.loads(dash.get("json_metadata") or "{}")

    chart_ids = {charts[spec["name"]] for spec in CHART_SPECS}
    remove_stale_chart_components(position, names, chart_ids)

    linked: dict[str, int] = {}
    for spec in CHART_SPECS:
        cid = charts[spec["name"]]
        comp_id = link_chart_by_name(
            position,
            spec["name"],
            cid,
            spec["tab"],
            spec["width"],
            spec["height"],
        )
        linked[spec["name"]] = cid
        print(f"  {spec['name']}: slice {cid} -> layout {comp_id}")

    fix_layout_parents(position)

    json_metadata["positions"] = position
    payload = {
        "dashboard_title": dash["dashboard_title"],
        "slug": dash.get("slug"),
        "owners": [owner_id],
        "position_json": json.dumps(position),
        "json_metadata": json.dumps(json_metadata),
    }
    resp = mutating_request(
        s,
        "PUT",
        f"{BASE}/api/v1/dashboard/{dashboard_id}",
        json=payload,
    )
    resp.raise_for_status()

    linked_ids = get_linked_chart_ids(s, BASE, dashboard_id)
    still_missing = [spec["name"] for spec in CHART_SPECS if charts[spec["name"]] not in linked_ids]
    if still_missing:
        print(f"WARN: dashboard API still missing charts: {still_missing}", file=sys.stderr)
        sys.exit(1)

    print(f"Linked charts {linked} to dashboard {dashboard_id}")


if __name__ == "__main__":
    main()
