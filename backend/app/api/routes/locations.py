"""
Geographic reference data — districts (and their real DB ids) + chiefdoms.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_any
from app.db.session import get_db
from app.models.location import Chiefdom, District
from app.models.user import User

router = APIRouter(tags=["locations"])


@router.get("/districts")
async def list_districts(db: AsyncSession = Depends(get_db), _: User = Depends(require_any)):
    """All districts with their real database ids (never guess ids client-side)."""
    rows = (await db.scalars(select(District).order_by(District.district_name))).all()
    return [{"id": d.id, "name": d.district_name} for d in rows]


@router.get("/districts/{district_id}/chiefdoms")
async def list_chiefdoms(
    district_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_any),
):
    rows = (await db.scalars(
        select(Chiefdom).where(Chiefdom.district_id == district_id).order_by(Chiefdom.chiefdom_name)
    )).all()
    return [{"id": c.id, "name": c.chiefdom_name} for c in rows]
