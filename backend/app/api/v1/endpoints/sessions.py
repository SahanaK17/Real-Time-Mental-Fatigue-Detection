"""Sessions API endpoints."""

from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models import User, TrackerSession, SessionStatus
from app.db.session import get_db

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/start", summary="Start a new tracking session")
async def start_session(
    hostname: Optional[str] = None,
    os_platform: Optional[str] = None,
    tracker_version: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # End any existing active session first
    await db.execute(
        update(TrackerSession)
        .where(
            TrackerSession.user_id == current_user.id, TrackerSession.status == SessionStatus.ACTIVE
        )
        .values(status=SessionStatus.INTERRUPTED, ended_at=datetime.now(timezone.utc))
    )

    session = TrackerSession(
        user_id=current_user.id,
        hostname=hostname,
        os_platform=os_platform,
        tracker_version=tracker_version,
        status=SessionStatus.ACTIVE,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return {
        "id": str(session.id),
        "status": session.status.value,
        "started_at": session.started_at.isoformat(),
    }


@router.post("/end", summary="End the current active session")
async def end_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrackerSession)
        .where(
            TrackerSession.user_id == current_user.id, TrackerSession.status == SessionStatus.ACTIVE
        )
        .order_by(desc(TrackerSession.started_at))
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"message": "No active session"}

    session.status = SessionStatus.COMPLETED
    session.ended_at = datetime.now(timezone.utc)
    session.duration_seconds = int((session.ended_at - session.started_at).total_seconds())
    await db.commit()

    return {
        "message": "Session ended",
        "session_id": str(session.id),
        "duration_s": session.duration_seconds,
    }


@router.get("/active", summary="Get current active session")
async def get_active_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrackerSession)
        .where(
            TrackerSession.user_id == current_user.id, TrackerSession.status == SessionStatus.ACTIVE
        )
        .order_by(desc(TrackerSession.started_at))
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if not session:
        return None
    return {
        "id": str(session.id),
        "status": session.status.value,
        "started_at": session.started_at.isoformat(),
        "hostname": session.hostname,
    }


@router.get("/", summary="List all sessions for current user")
async def list_sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(TrackerSession)
        .where(TrackerSession.user_id == current_user.id)
        .order_by(desc(TrackerSession.started_at))
        .offset(offset)
        .limit(page_size)
    )
    sessions = result.scalars().all()

    return {
        "page": page,
        "sessions": [
            {
                "id": str(s.id),
                "status": s.status.value,
                "started_at": s.started_at.isoformat(),
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "duration_seconds": s.duration_seconds,
                "avg_fatigue_score": s.avg_fatigue_score,
            }
            for s in sessions
        ],
    }
