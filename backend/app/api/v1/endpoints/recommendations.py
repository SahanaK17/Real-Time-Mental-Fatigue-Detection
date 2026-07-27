"""Recommendations, Analytics, Admin, Notifications, Users endpoint stubs."""

# recommendations.py
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.db.models import User, Recommendation
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/", summary="Get active recommendations for current user")
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recommendation)
        .where(
            Recommendation.user_id == current_user.id,
            Recommendation.is_dismissed == False,
            Recommendation.is_completed == False,
        )
        .order_by(desc(Recommendation.created_at))
        .limit(5)
    )
    recs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "description": r.description,
            "category": r.category,
            "icon": r.icon,
            "priority": r.priority,
            "duration_minutes": r.duration_minutes,
            "created_at": r.created_at.isoformat(),
        }
        for r in recs
    ]


@router.post("/{recommendation_id}/dismiss")
async def dismiss_recommendation(
    recommendation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone

    result = await db.execute(
        select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == current_user.id,
        )
    )
    rec = result.scalar_one_or_none()
    if rec:
        rec.is_dismissed = True
        rec.dismissed_at = datetime.now(timezone.utc)
        await db.commit()
    return {"message": "Dismissed"}


@router.post("/{recommendation_id}/complete")
async def complete_recommendation(
    recommendation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone

    result = await db.execute(
        select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == current_user.id,
        )
    )
    rec = result.scalar_one_or_none()
    if rec:
        rec.is_completed = True
        rec.completed_at = datetime.now(timezone.utc)
        await db.commit()
    return {"message": "Completed"}
