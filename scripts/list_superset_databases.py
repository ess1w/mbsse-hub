#!/usr/bin/env python3
"""
List Preset/Superset database connections and dashboard ids.

Preset workspace example:
  SUPERSET_URL='https://83f65675.us2a.app.preset.io' \\
  PRESET_API_TOKEN='...' \\
  PRESET_API_SECRET='...' \\
  python3 list_superset_databases.py

Self-hosted example:
  SUPERSET_URL=http://127.0.0.1:8088 \\
  SUPERSET_USER=admin SUPERSET_PASSWORD=admin \\
  python3 list_superset_databases.py

You can paste a full Preset UI URL — the script strips it to the workspace base.
API keys: manage.app.preset.io → your profile → API Keys (same keys as Render embed).
"""

from __future__ import annotations

import json
import os
import sys

from superset_auth import login_session, normalize_workspace_url, resolve_dashboard_id


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    raw_url = os.environ.get("SUPERSET_URL", "")
    base = normalize_workspace_url(raw_url)
    if not base:
        fail("SUPERSET_URL is not set.")

    has_preset = bool(os.environ.get("PRESET_API_TOKEN") and os.environ.get("PRESET_API_SECRET"))
    has_password = bool(os.environ.get("SUPERSET_USER") and os.environ.get("SUPERSET_PASSWORD"))

    print(f"Workspace: {base}")
    if raw_url and raw_url.rstrip("/") != base:
        print(f"  (normalized from {raw_url.split('?')[0]})")
    print(f"Auth: {'Preset API token' if has_preset else 'username/password' if has_password else 'NONE'}")

    if not has_preset and not has_password:
        fail(
            "Set Preset API credentials (recommended):\n"
            "  PRESET_API_TOKEN=... PRESET_API_SECRET=...\n"
            "Generate at https://manage.app.preset.io/app/user → API Keys\n"
            "Or set SUPERSET_USER + SUPERSET_PASSWORD for self-hosted Superset."
        )

    try:
        session = login_session(base)
    except RuntimeError as exc:
        fail(str(exc))

    print("Login: OK\n")

    db_resp = session.get(f"{base}/api/v1/database/", timeout=30)
    print(f"Database list HTTP {db_resp.status_code}")
    if db_resp.status_code != 200:
        fail(db_resp.text[:500])

    databases = db_resp.json().get("result", [])
    if not databases:
        print("No database connections found.")
    else:
        print("Database connections — use id as SUPERSET_DB_ID:\n")
        for db in databases:
            print(
                f"  SUPERSET_DB_ID={db.get('id')}  "
                f"name={db.get('database_name')!r}  "
                f"backend={db.get('backend')}"
            )

    dash_ref = os.environ.get("SUPERSET_DASHBOARD_ID") or os.environ.get(
        "PRESET_DASHBOARD_ID", "oBMOvaLJDme"
    )
    print(f"\nLooking up dashboard {dash_ref!r} ...")
    try:
        dash_id = resolve_dashboard_id(session, dash_ref)
        dash_resp = session.get(f"{base}/api/v1/dashboard/{dash_id}", timeout=30)
        dash_resp.raise_for_status()
        dash = dash_resp.json()["result"]
        print(
            f"  SUPERSET_DASHBOARD_ID={dash_id}  "
            f"title={dash.get('dashboard_title')!r}  "
            f"slug={dash.get('slug')!r}"
        )
    except Exception as exc:
        print(f"  Could not resolve dashboard: {exc}")

    print("\nExample run:")
    db_example = databases[0]["id"] if databases else "<id>"
    print(
        f"  SUPERSET_URL='{base}' \\\n"
        f"  PRESET_API_TOKEN='...' PRESET_API_SECRET='...' \\\n"
        f"  SUPERSET_DB_ID={db_example} \\\n"
        f"  SUPERSET_DASHBOARD_ID={dash_ref} \\\n"
        f"  python3 fix_superset_sql_v2.py"
    )


if __name__ == "__main__":
    main()
