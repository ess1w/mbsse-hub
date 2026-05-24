from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import get_settings
from app.api.routes import auth, submissions, organisations

settings = get_settings()

app = FastAPI(
    title="MBSSE School Safety Coordination Hub",
    description="API for partner reporting, coordination, and monitoring.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    # allow_credentials must be False when allow_origins contains "*".
    # Bearer tokens sent via the Authorization header work fine without it
    # (credentials=True is only needed for cookies / browser-managed auth).
    allow_credentials=settings.origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1")
app.include_router(submissions.router, prefix="/api/v1")
app.include_router(organisations.router, prefix="/api/v1")

# ── Serve local uploads in dev ────────────────────────────────────────────────
if settings.storage_backend == "local":
    os.makedirs(settings.local_upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.local_upload_dir), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.environment}
