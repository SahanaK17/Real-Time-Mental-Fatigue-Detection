"""
Predictions API — Stub for remaining endpoints
GET /predictions/latest     — Latest prediction for current session
GET /predictions/history    — Historical predictions (paginated)
GET /predictions/{id}       — Get prediction details with SHAP
"""

from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.db.models import FatiguePrediction, User
from app.db.session import get_db

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/latest", summary="Get the latest fatigue prediction")
async def get_latest_prediction(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FatiguePrediction)
        .where(FatiguePrediction.user_id == current_user.id)
        .order_by(desc(FatiguePrediction.predicted_at))
        .limit(1)
    )
    prediction = result.scalar_one_or_none()
    if not prediction:
        return None

    return {
        "id": str(prediction.id),
        "fatigue_score": prediction.fatigue_score,
        "fatigue_level": prediction.fatigue_level.value,
        "confidence": prediction.confidence,
        "model_name": prediction.model_name,
        "top_features": prediction.top_features,
        "shap_values": prediction.shap_values,
        "explanation_text": prediction.explanation_text,
        "predicted_at": prediction.predicted_at.isoformat(),
    }


@router.get("/history", summary="Get prediction history")
async def get_prediction_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    session_id: Optional[UUID] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    query = select(FatiguePrediction).where(FatiguePrediction.user_id == current_user.id)

    if session_id:
        query = query.where(FatiguePrediction.session_id == session_id)

    query = query.order_by(desc(FatiguePrediction.predicted_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    predictions = result.scalars().all()

    return {
        "page": page,
        "page_size": page_size,
        "predictions": [
            {
                "id": str(p.id),
                "fatigue_score": p.fatigue_score,
                "fatigue_level": p.fatigue_level.value,
                "confidence": p.confidence,
                "predicted_at": p.predicted_at.isoformat(),
            }
            for p in predictions
        ],
    }
