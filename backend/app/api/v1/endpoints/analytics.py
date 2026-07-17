"""
Analytics API Endpoints
========================
GET /analytics/daily     — Daily fatigue trend for current user
GET /analytics/weekly    — Weekly aggregated statistics
GET /analytics/monthly   — Monthly aggregated statistics
GET /analytics/heatmap   — Hourly fatigue heatmap (for visualization)
GET /analytics/summary   — Overall summary stats
"""

from datetime import datetime, timedelta, timezone, date
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, extract, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models import FatiguePrediction, BehaviourSnapshot, User
from app.db.session import get_db

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/summary", summary="Get overall analytics summary for the current user")
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns key statistics for the current user's dashboard."""
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc)
    week_start = today_start - timedelta(days=7)

    # Today's stats
    today_result = await db.execute(
        select(
            func.avg(FatiguePrediction.fatigue_score),
            func.max(FatiguePrediction.fatigue_score),
            func.count(FatiguePrediction.id),
        ).where(
            FatiguePrediction.user_id == current_user.id,
            FatiguePrediction.predicted_at >= today_start,
        )
    )
    today_avg, today_max, today_count = today_result.first()

    # Weekly stats
    week_result = await db.execute(
        select(func.avg(FatiguePrediction.fatigue_score)).where(
            FatiguePrediction.user_id == current_user.id,
            FatiguePrediction.predicted_at >= week_start,
        )
    )
    week_avg = week_result.scalar()

    # Latest prediction
    latest_result = await db.execute(
        select(FatiguePrediction)
        .where(FatiguePrediction.user_id == current_user.id)
        .order_by(FatiguePrediction.predicted_at.desc())
        .limit(1)
    )
    latest = latest_result.scalar_one_or_none()

    return {
        "today": {
            "avg_fatigue_score": round(today_avg or 0.0, 3),
            "max_fatigue_score": round(today_max or 0.0, 3),
            "prediction_count": today_count or 0,
        },
        "week": {
            "avg_fatigue_score": round(week_avg or 0.0, 3),
        },
        "current": {
            "fatigue_score": latest.fatigue_score if latest else None,
            "fatigue_level": latest.fatigue_level.value if latest else None,
            "confidence": latest.confidence if latest else None,
            "predicted_at": latest.predicted_at.isoformat() if latest else None,
            "top_features": latest.top_features if latest else [],
            "explanation": latest.explanation_text if latest else None,
        },
    }


@router.get("/daily", summary="Hourly fatigue trend for today")
async def get_daily_trend(
    target_date: Optional[date] = Query(default=None, description="Date (YYYY-MM-DD), defaults to today"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns hourly average fatigue scores for the specified date."""
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    day_start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    result = await db.execute(
        select(
            extract("hour", FatiguePrediction.predicted_at).label("hour"),
            func.avg(FatiguePrediction.fatigue_score).label("avg_score"),
            func.count(FatiguePrediction.id).label("count"),
        )
        .where(
            FatiguePrediction.user_id == current_user.id,
            FatiguePrediction.predicted_at >= day_start,
            FatiguePrediction.predicted_at < day_end,
        )
        .group_by("hour")
        .order_by("hour")
    )
    rows = result.all()

    return {
        "date": str(target_date),
        "hourly": [
            {
                "hour": int(row.hour),
                "avg_fatigue_score": round(float(row.avg_score), 3),
                "count": int(row.count),
            }
            for row in rows
        ],
    }


@router.get("/weekly", summary="Daily fatigue trend for the past 7 days")
async def get_weekly_trend(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns daily average fatigue scores for the past 7 days."""
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)

    result = await db.execute(
        select(
            func.date(FatiguePrediction.predicted_at).label("day"),
            func.avg(FatiguePrediction.fatigue_score).label("avg_score"),
            func.max(FatiguePrediction.fatigue_score).label("max_score"),
            func.count(FatiguePrediction.id).label("count"),
        )
        .where(
            FatiguePrediction.user_id == current_user.id,
            FatiguePrediction.predicted_at >= week_start,
        )
        .group_by("day")
        .order_by("day")
    )
    rows = result.all()

    return {
        "period": "7_days",
        "daily": [
            {
                "date": str(row.day),
                "avg_fatigue_score": round(float(row.avg_score), 3),
                "max_fatigue_score": round(float(row.max_score), 3),
                "prediction_count": int(row.count),
            }
            for row in rows
        ],
    }


@router.get("/heatmap", summary="Hour-of-day vs day-of-week fatigue heatmap")
async def get_heatmap(
    days: int = Query(default=30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns a 24x7 heatmap of average fatigue scores."""
    start = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            extract("hour", FatiguePrediction.predicted_at).label("hour"),
            extract("dow", FatiguePrediction.predicted_at).label("day_of_week"),
            func.avg(FatiguePrediction.fatigue_score).label("avg_score"),
        )
        .where(
            FatiguePrediction.user_id == current_user.id,
            FatiguePrediction.predicted_at >= start,
        )
        .group_by("hour", "day_of_week")
        .order_by("day_of_week", "hour")
    )
    rows = result.all()

    return {
        "period_days": days,
        "heatmap": [
            {
                "hour": int(row.hour),
                "day_of_week": int(row.day_of_week),
                "avg_fatigue_score": round(float(row.avg_score), 3),
            }
            for row in rows
        ],
    }
