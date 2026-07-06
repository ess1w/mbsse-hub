"""Authenticate to self-hosted Superset or Preset workspaces."""

from __future__ import annotations

import os
import re
from typing import Any

import requests

# API keys from manage.app.preset.io — works for workspace + embedding on Professional.
# api.app.preset.io is Enterprise-only (org/team management API).
PRESET_AUTH_URL = os.environ.get(
    "PRESET_AUTH_URL",
    "https://manage.app.preset.io/api/v1/auth/",
)


def normalize_workspace_url(url: str) -> str:
    """Accept Preset UI URLs and return the workspace base."""
    url = url.strip().rstrip("/")
    if not url:
        return url
    match = re.match(r"(https?://[^/]+\.app\.preset\.io)", url)
    if match:
        return match.group(1)
    match = re.match(r"(https?://[^/]+\.superset\.app)", url)
    if match:
        return match.group(1)
    match = re.match(r"(https?://[^/]+)", url)
    return match.group(1) if match else url


def is_preset_workspace(base: str) -> bool:
    return ".app.preset.io" in base


def preset_access_token(api_token: str, api_secret: str) -> str:
    resp = requests.post(
        PRESET_AUTH_URL,
        json={"name": api_token, "secret": api_secret},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Preset API auth failed ({resp.status_code}): {resp.text[:300]}"
        )
    return resp.json()["payload"]["access_token"]


def refresh_csrf(session: requests.Session, base: str) -> None:
    """Fetch CSRF for self-hosted Superset (username/password login)."""
    csrf_resp = session.get(
        f"{base}/api/v1/security/csrf_token/",
        headers={"Referer": f"{base}/"},
        timeout=30,
    )
    if csrf_resp.status_code != 200:
        raise RuntimeError(
            f"CSRF fetch failed ({csrf_resp.status_code}): {csrf_resp.text[:300]}"
        )
    csrf = csrf_resp.json().get("result")
    if not csrf:
        raise RuntimeError("CSRF endpoint returned no token")
    session.headers["X-CSRFToken"] = csrf
    session.headers["Referer"] = f"{base}/"


def login_session(base_url: str | None = None) -> requests.Session:
    """
    Return an authenticated requests session.

    Preset workspace (.app.preset.io):
      SUPERSET_URL=https://83f65675.us2a.app.preset.io
      PRESET_API_TOKEN=...
      PRESET_API_SECRET=...
      Do NOT set SUPERSET_USER/PASSWORD — Preset blocks /api/v1/security/login.
      Auth uses manage.app.preset.io (Professional). Override with PRESET_AUTH_URL
      only if Preset directs you to a different endpoint.

    Self-hosted Superset:
      SUPERSET_URL=http://localhost:8088
      SUPERSET_USER=admin
      SUPERSET_PASSWORD=admin
    """
    base = normalize_workspace_url(base_url or os.environ.get("SUPERSET_URL", ""))
    if not base:
        raise RuntimeError("SUPERSET_URL is not set.")

    preset_token = os.environ.get("PRESET_API_TOKEN", "")
    preset_secret = os.environ.get("PRESET_API_SECRET", "")
    user = os.environ.get("SUPERSET_USER", "")
    password = os.environ.get("SUPERSET_PASSWORD", "")

    if is_preset_workspace(base) and user and password:
        raise RuntimeError(
            "Preset workspaces do not support SUPERSET_USER/PASSWORD API login.\n"
            "Remove those variables and use PRESET_API_TOKEN + PRESET_API_SECRET only."
        )

    session = requests.Session()
    session.headers["Content-Type"] = "application/json"
    session.headers["Referer"] = f"{base}/"
    session.headers["User-Agent"] = "MBSSE Superset scripts"

    if preset_token and preset_secret:
        jwt = preset_access_token(preset_token, preset_secret)
        session.headers["Authorization"] = f"Bearer {jwt}"
        # Preset accepts Bearer JWT for mutating calls without CSRF headers
        # (same as preset-cli JWTAuth / SupersetClient).
        session.headers.pop("X-CSRFToken", None)
        session.preset_jwt = True  # type: ignore[attr-defined]
    elif user and password:
        resp = session.post(
            f"{base}/api/v1/security/login",
            json={
                "username": user,
                "password": password,
                "provider": "db",
                "refresh": True,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Superset login failed ({resp.status_code}): {resp.text[:300]}"
            )
        session.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"
        session.preset_jwt = False  # type: ignore[attr-defined]
        refresh_csrf(session, base)
    else:
        raise RuntimeError(
            "Set PRESET_API_TOKEN + PRESET_API_SECRET for Preset, "
            "or SUPERSET_USER + SUPERSET_PASSWORD for self-hosted Superset."
        )

    session.base_url = base  # type: ignore[attr-defined]
    return session


def mutating_request(
    session: requests.Session,
    method: str,
    url: str,
    **kwargs: Any,
) -> requests.Response:
    """POST/PUT/DELETE — CSRF refresh only for self-hosted Superset."""
    if not getattr(session, "preset_jwt", False):
        base = getattr(session, "base_url", normalize_workspace_url(url))
        refresh_csrf(session, base)
    else:
        session.headers.pop("X-CSRFToken", None)
    return session.request(method, url, **kwargs)


def resolve_dashboard_id(session: requests.Session, dashboard_ref: str) -> int:
    """Resolve numeric dashboard id from an integer id or slug."""
    if dashboard_ref.isdigit():
        return int(dashboard_ref)

    base = session.base_url  # type: ignore[attr-defined]
    resp = session.get(
        f"{base}/api/v1/dashboard/",
        params={
            "q": __import__("json").dumps(
                {
                    "filters": [{"col": "slug", "opr": "eq", "value": dashboard_ref}],
                    "page_size": 1,
                }
            )
        },
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json().get("result", [])
    if not results:
        raise RuntimeError(
            f"Dashboard slug {dashboard_ref!r} not found. "
            "List dashboards in Preset or pass the numeric SUPERSET_DASHBOARD_ID."
        )
    return results[0]["id"]


def resolve_owner_id(session: requests.Session) -> int:
    if env_id := os.environ.get("SUPERSET_OWNER_ID"):
        return int(env_id)

    base = session.base_url  # type: ignore[attr-defined]
    for path in ("/api/v1/me/", "/api/v1/me"):
        resp = session.get(f"{base}{path}", timeout=30)
        if resp.status_code == 200:
            result = resp.json().get("result", resp.json())
            if user_id := result.get("id"):
                return int(user_id)
    return 1
