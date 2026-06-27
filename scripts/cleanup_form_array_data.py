#!/usr/bin/env python3
"""
Clean up bad array values saved from the reporting form (test saves).

Fixes:
  - objectives: full form text / "Obj 1" -> obj1, obj2, obj3
  - focus_areas: numbered duplicates -> short canonical labels
  - districts: blank / invalid -> removed; empty arrays backfilled from
    submission_locations or organisation registry

Usage:
  # Preview changes (local):
  DATABASE_URL=postgresql://mbsse:password@localhost:5432/mbsse_hub \\
    python3 cleanup_form_array_data.py

  # Apply on Render (use External Database URL, sync driver):
  DATABASE_URL='postgresql://...' python3 cleanup_form_array_data.py --apply

  Or with discrete vars:
  PGHOST=... PGUSER=... PGPASSWORD=... PGDATABASE=mbsse_hub python3 cleanup_form_array_data.py --apply
"""

from __future__ import annotations

import argparse
import os
import re
import sys

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Install psycopg2-binary: pip install psycopg2-binary", file=sys.stderr)
    raise

# Canonical focus-area labels (match seed data / chart display; no leading numbers)
FOCUS_AREA_CANONICAL = {
    "1. SRGBV Prevention & Response": "SRGBV Prevention & Response",
    "2. MHPSS": "MHPSS",
    "3. School Governance": "School Governance",
    "4. Life Skills / SRH": "Life Skills / SRH",
    "5. WASH": "WASH",
    "6. Social Norms": "Social Norms",
    "7. Social Protection": "Social Protection",
    "8. Other": "Other",
}

JUNK_DISTRICTS = {"", "(unknown)", "unknown", "(Unknown)", "N/A", "n/a", "null", "NULL"}


def parse_database_url(url: str) -> dict[str, str]:
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgres://", "postgresql://")
    from urllib.parse import urlparse

    p = urlparse(url)
    return {
        "host": p.hostname or "localhost",
        "port": str(p.port or 5432),
        "dbname": (p.path or "/mbsse_hub").lstrip("/"),
        "user": p.username or "mbsse",
        "password": p.password or "",
    }


def connect() -> psycopg2.extensions.connection:
    url = os.environ.get("DATABASE_URL")
    if url:
        return psycopg2.connect(**parse_database_url(url))
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ.get("PGDATABASE", "mbsse_hub"),
        user=os.environ.get("PGUSER", "mbsse"),
        password=os.environ.get("PGPASSWORD", ""),
    )


def normalize_objective(val: str) -> str:
    v = val.strip()
    lower = v.lower()
    if v in ("obj1", "Obj 1") or lower == "obj 1" or re.match(r"^obj\s*1$", lower, re.I):
        return "obj1"
    if v in ("obj2", "Obj 2") or lower == "obj 2" or re.match(r"^obj\s*2$", lower, re.I):
        return "obj2"
    if v in ("obj3", "Obj 3") or lower == "obj 3" or re.match(r"^obj\s*3$", lower, re.I):
        return "obj3"
    if re.match(r"^1[.:]", v) or "promote gender equitable" in lower:
        return "obj1"
    if re.match(r"^2[.:]", v) or "strengthen institutional" in lower:
        return "obj2"
    if re.match(r"^3[.:]", v) or "sustained commitment" in lower:
        return "obj3"
    return v


def normalize_focus_area(val: str) -> str:
    v = val.strip()
    if v in FOCUS_AREA_CANONICAL:
        return FOCUS_AREA_CANONICAL[v]
    m = re.match(r"^\d+\.\s+(.*)$", v)
    if m:
        tail = m.group(1).strip()
        for canonical in FOCUS_AREA_CANONICAL.values():
            if canonical.lower() == tail.lower():
                return canonical
        return tail
    return v


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def clean_string_array(
    values: list[str] | None,
    normalizer,
    valid: set[str] | None = None,
) -> list[str]:
    if not values:
        return []
    cleaned: list[str] = []
    for raw in values:
        if raw is None:
            continue
        v = normalizer(str(raw).strip())
        if not v or v in JUNK_DISTRICTS:
            continue
        if valid is not None and v not in valid:
            continue
        cleaned.append(v)
    return dedupe_preserve_order(cleaned)


def fetch_valid_districts(cur) -> set[str]:
    cur.execute("SELECT district_name FROM districts ORDER BY 1")
    return {r["district_name"] for r in cur.fetchall()}


def report_distinct(cur, label: str, sql: str) -> None:
    cur.execute(sql)
    rows = cur.fetchall()
    print(f"\n{label} ({len(rows)} distinct):")
    for r in rows[:30]:
        val = r["v"] if isinstance(r, dict) else r[0]
        print(f"  {val!r}")
    if len(rows) > 30:
        print(f"  ... and {len(rows) - 30} more")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean form array data in mbsse_hub")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes (default is dry-run preview only)",
    )
    args = parser.parse_args()

    conn = connect()
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    valid_districts = fetch_valid_districts(cur)
    print(f"Valid districts: {len(valid_districts)}")

    if not args.apply:
        print("\n=== DRY RUN (pass --apply to write) ===")
        report_distinct(
            cur,
            "Objectives (before)",
            "SELECT DISTINCT unnest(objectives) AS v FROM activities ORDER BY 1",
        )
        report_distinct(
            cur,
            "Focus areas (before)",
            "SELECT DISTINCT unnest(focus_areas) AS v FROM activities ORDER BY 1",
        )
        report_distinct(
            cur,
            "Activity districts (before)",
            """
            SELECT DISTINCT d AS v FROM activities,
              LATERAL unnest(COALESCE(districts, ARRAY[]::varchar[])) AS d
            ORDER BY 1
            """,
        )

    # --- activities ---
    cur.execute(
        """
        SELECT a.activity_id, a.objectives, a.focus_areas, a.districts,
               s.id AS submission_id, o.districts AS org_districts
        FROM activities a
        JOIN submissions s ON s.id = a.submission_id
        JOIN organisations o ON o.org_id = s.org_id
        """
    )
    activities = cur.fetchall()

    cur.execute(
        """
        SELECT submission_id,
               array_agg(DISTINCT district_name ORDER BY district_name)
                 FILTER (WHERE district_name IS NOT NULL AND trim(district_name) <> '')
                 AS loc_districts
        FROM submission_locations
        GROUP BY submission_id
        """
    )
    loc_by_sub = {r["submission_id"]: r["loc_districts"] or [] for r in cur.fetchall()}

    act_updates = 0
    for row in activities:
        new_obj = clean_string_array(row["objectives"], normalize_objective)
        new_fa = clean_string_array(row["focus_areas"], normalize_focus_area)
        new_dist = clean_string_array(
            row["districts"],
            lambda x: x.strip(),
            valid=valid_districts,
        )
        if not new_dist:
            loc = loc_by_sub.get(row["submission_id"], [])
            loc_clean = clean_string_array(loc, lambda x: x.strip(), valid=valid_districts)
            org_clean = clean_string_array(
                row["org_districts"], lambda x: x.strip(), valid=valid_districts
            )
            new_dist = loc_clean or org_clean

        changed = (
            new_obj != (row["objectives"] or [])
            or new_fa != (row["focus_areas"] or [])
            or new_dist != (row["districts"] or [])
        )
        if changed:
            act_updates += 1
            if args.apply:
                cur.execute(
                    """
                    UPDATE activities
                    SET objectives = %s, focus_areas = %s, districts = %s
                    WHERE activity_id = %s
                    """,
                    (new_obj, new_fa, new_dist, row["activity_id"]),
                )

    print(f"\nActivities to update: {act_updates}")

    # --- organisations.districts ---
    cur.execute("SELECT org_id, districts FROM organisations")
    org_updates = 0
    for row in cur.fetchall():
        new_dist = clean_string_array(
            row["districts"], lambda x: x.strip(), valid=valid_districts
        )
        if new_dist != (row["districts"] or []):
            org_updates += 1
            if args.apply:
                cur.execute(
                    "UPDATE organisations SET districts = %s WHERE org_id = %s",
                    (new_dist, row["org_id"]),
                )
    print(f"Organisations to update: {org_updates}")

    # --- submission_locations ---
    cur.execute(
        "SELECT location_id, submission_id, district_name FROM submission_locations"
    )
    loc_updates = 0
    loc_deletes = 0
    for row in cur.fetchall():
        name = (row["district_name"] or "").strip()
        if not name or name in JUNK_DISTRICTS or name not in valid_districts:
            loc_deletes += 1
            if args.apply:
                cur.execute(
                    "DELETE FROM submission_locations WHERE location_id = %s",
                    (row["location_id"],),
                )
        elif name != row["district_name"]:
            loc_updates += 1
            if args.apply:
                cur.execute(
                    "UPDATE submission_locations SET district_name = %s WHERE location_id = %s",
                    (name, row["location_id"]),
                )
    print(f"Submission locations to fix: {loc_updates}, delete junk: {loc_deletes}")

    # --- output_indicators.district_name (non-empty junk only) ---
    cur.execute(
        """
        SELECT activity_id, district_name FROM output_indicators
        WHERE trim(district_name) <> ''
        """
    )
    oi_updates = 0
    for row in cur.fetchall():
        name = row["district_name"].strip()
        if name in JUNK_DISTRICTS or name not in valid_districts:
            oi_updates += 1
            if args.apply:
                cur.execute(
                    """
                    UPDATE output_indicators SET district_name = ''
                    WHERE activity_id = %s AND district_name = %s
                    """,
                    (row["activity_id"], row["district_name"]),
                )
    print(f"Output indicator district rows to reset: {oi_updates}")

    # --- training_by_focus_area (if migration 0003 applied) ---
    cur.execute(
        """
        SELECT EXISTS (
          SELECT 1 FROM information_schema.tables
          WHERE table_schema = 'public' AND table_name = 'training_by_focus_area'
        ) AS ok
        """
    )
    if cur.fetchone()["ok"]:
        cur.execute(
            """
            SELECT activity_id, district_name, focus_area, cadre
            FROM training_by_focus_area
            """
        )
        tr_updates = 0
        for row in cur.fetchall():
            fa = normalize_focus_area(row["focus_area"] or "")
            dist = (row["district_name"] or "").strip()
            if dist in JUNK_DISTRICTS or (dist and dist not in valid_districts):
                dist = ""
            if fa != row["focus_area"] or dist != (row["district_name"] or ""):
                tr_updates += 1
                if args.apply:
                    cur.execute(
                        """
                        UPDATE training_by_focus_area
                        SET focus_area = %s, district_name = %s
                        WHERE activity_id = %s AND district_name = %s
                          AND focus_area = %s AND cadre = %s
                        """,
                        (
                            fa,
                            dist,
                            row["activity_id"],
                            row["district_name"],
                            row["focus_area"],
                            row["cadre"],
                        ),
                    )
        print(f"Training rows to update: {tr_updates}")
    else:
        print("Training table not present (skip)")

    # --- projects.focus_area ---
    cur.execute(
        """
        SELECT EXISTS (
          SELECT 1 FROM information_schema.columns
          WHERE table_schema = 'public' AND table_name = 'projects'
            AND column_name = 'focus_area'
        ) AS ok
        """
    )
    if cur.fetchone()["ok"]:
        cur.execute("SELECT project_id, focus_area FROM projects")
        proj_updates = 0
        for row in cur.fetchall():
            new_fa = clean_string_array(row["focus_area"], normalize_focus_area)
            if new_fa != (row["focus_area"] or []):
                proj_updates += 1
                if args.apply:
                    cur.execute(
                        "UPDATE projects SET focus_area = %s WHERE project_id = %s",
                        (new_fa, row["project_id"]),
                    )
        print(f"Projects to update: {proj_updates}")

    if args.apply:
        conn.commit()
        print("\nCommitted.")
        report_distinct(
            cur,
            "Objectives (after)",
            "SELECT DISTINCT unnest(objectives) AS v FROM activities ORDER BY 1",
        )
        report_distinct(
            cur,
            "Focus areas (after)",
            "SELECT DISTINCT unnest(focus_areas) AS v FROM activities ORDER BY 1",
        )
        report_distinct(
            cur,
            "Activity districts (after)",
            """
            SELECT DISTINCT d AS v FROM activities,
              LATERAL unnest(COALESCE(districts, ARRAY[]::varchar[])) AS d
            ORDER BY 1
            """,
        )
    else:
        conn.rollback()
        print("\nDry run complete — re-run with --apply to write changes.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
