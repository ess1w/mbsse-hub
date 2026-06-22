"""
GET /analytics/guest-token

Returns a short-lived Preset guest token that the frontend uses with the
@superset-ui/embedded-sdk to render the analytics dashboard in an iframe.

Flow:
  1. Exchange PRESET_API_TOKEN + PRESET_API_SECRET for a Preset access token
  2. Use the access token to request a guest token for the configured dashboard
  3. Return the guest token to the caller (valid ~5 minutes)

Environment variables required (set in Render dashboard):
  PRESET_API_TOKEN      – token from manage.app.preset.io → user settings → API Keys
  PRESET_API_SECRET     – secret from the same page (only shown once)
  PRESET_TEAM           – team name (default: MBSSE)
  PRESET_WORKSPACE      – workspace name (default: SRGBV Hub)
  PRESET_DASHBOARD_ID   – dashboard slug from the Preset URL (default: oBMOvaLJDme)
"""
import httpx
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.security import decode_token

router = APIRouter(prefix="/analytics", tags=["analytics"])
bearer = HTTPBearer()

PRESET_AUTH_URL   = "https://api.app.preset.io/v1/auth/"
PRESET_GUEST_URL  = "https://api.app.preset.io/v1/teams/{team}/workspaces/{workspace}/guest-token/"


async def _get_preset_access_token(token: str, secret: str) -> str:
    """Exchange Preset API key + secret for a short-lived access token."""
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            PRESET_AUTH_URL,
            json={"name": token, "secret": secret},
        )
    if res.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Preset auth failed ({res.status_code}): {res.text[:200]}",
        )
    return res.json()["payload"]["access_token"]


@router.get("/guest-token")
async def get_guest_token(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
):
    """Return a Preset guest token for the embedded analytics dashboard.

    Requires a valid Hub JWT (any role) — this prevents unauthenticated
    users from minting guest tokens.
    """
    # Validate the caller's Hub JWT
    try:
        decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    settings = get_settings()

    if not settings.preset_api_token or not settings.preset_api_secret:
        raise HTTPException(
            status_code=503,
            detail="Preset API credentials not configured (PRESET_API_TOKEN / PRESET_API_SECRET)",
        )

    # Step 1 — get Preset access token
    access_token = await _get_preset_access_token(
        settings.preset_api_token, settings.preset_api_secret
    )

    # Step 2 — mint a guest token for the dashboard
    # Use workspace slug if set, otherwise fall back to display name
    workspace_id = settings.preset_workspace_slug or settings.preset_workspace
    team      = quote(settings.preset_team, safe="")
    workspace = quote(workspace_id, safe="")
    url       = PRESET_GUEST_URL.format(team=team, workspace=workspace)

    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "user": {
                    "username": "mbsse-hub-embed",
                    "first_name": "MBSSE",
                    "last_name":  "Hub",
                },
                "resources": [
                    {"type": "dashboard", "id": settings.preset_dashboard_id}
                ],
                "rls": [],
                "enable_drilling": False,
            },
        )

    if res.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Preset guest token request failed ({res.status_code}): {res.text[:200]}",
        )

    return {"token": res.json()["payload"]["token"]}
