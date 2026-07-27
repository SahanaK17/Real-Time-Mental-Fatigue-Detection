"""
Behaviour Ingestion API
========================
POST /behaviour/snapshot  — Submit a 1-second behaviour window
POST /behaviour/batch     — Submit multiple snapshots (batch)
GET  /behaviour/current   — Get most recent snapshot for active session
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.models import BehaviourSnapshot, TrackerSession, User, SessionStatus
from app.db.session import get_db
from app.schemas.behaviour import BehaviourSnapshotCreate, BehaviourSnapshotResponse
from app.services.prediction_service import PredictionService
from app.websocket.manager import ws_manager
from sqlalchemy import select

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post(
    "/snapshot",
    response_model=BehaviourSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a behavioural data snapshot (1-second window)",
)
async def submit_snapshot(
    payload: BehaviourSnapshotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a 1-second aggregated window of keyboard and mouse metrics.
    Triggers real-time ML inference and broadcasts result via WebSocket.
    """
    # Validate session belongs to user and is active
    result = await db.execute(
        select(TrackerSession).where(
            TrackerSession.id == payload.session_id,
            TrackerSession.user_id == current_user.id,
            TrackerSession.status == SessionStatus.ACTIVE,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Active session", payload.session_id)

    # Create snapshot
    snapshot = BehaviourSnapshot(
        session_id=payload.session_id,
        user_id=current_user.id,
        **payload.model_dump(exclude={"session_id"}),
    )
    db.add(snapshot)
    await db.flush()

    # Run ML inference asynchronously
    prediction_service = PredictionService()
    prediction = await prediction_service.predict_and_save(
        snapshot=snapshot,
        user=current_user,
        session=session,
        db=db,
    )

    await db.commit()
    await db.refresh(snapshot)

    # Broadcast via WebSocket if prediction was made
    if prediction:
        import json

        await ws_manager.broadcast_to_user(
            str(current_user.id),
            json.dumps(
                {
                    "type": "fatigue_update",
                    "fatigue_score": prediction.fatigue_score,
                    "fatigue_level": prediction.fatigue_level.value,
                    "confidence": prediction.confidence,
                    "top_features": prediction.top_features,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
        )

    return snapshot


@router.post(
    "/batch",
    status_code=status.HTTP_201_CREATED,
    summary="Submit multiple snapshots in one request (batch upload)",
)
async def submit_batch(
    snapshots: List[BehaviourSnapshotCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Batch upload for offline/buffered tracking.
    Processes snapshots sequentially, returns summary.
    """
    if len(snapshots) > 300:  # Max 5 minutes of data per batch
        from app.core.exceptions import ValidationError

        raise ValidationError("Maximum 300 snapshots per batch request")

    created_count = 0
    for payload in snapshots:
        snapshot = BehaviourSnapshot(
            session_id=payload.session_id,
            user_id=current_user.id,
            **payload.model_dump(exclude={"session_id"}),
        )
        db.add(snapshot)
        created_count += 1

    await db.commit()
    return {"created": created_count, "message": f"Successfully ingested {created_count} snapshots"}
