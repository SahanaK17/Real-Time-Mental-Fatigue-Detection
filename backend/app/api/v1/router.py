"""
API v1 Router
=============
Aggregates all endpoint routers under /api/v1/.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    behaviour,
    analytics,
    predictions,
    recommendations,
    notifications,
    users,
    admin,
    sessions,
)

api_router = APIRouter()

# Auth
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User management
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Sessions
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])

# Behaviour ingestion
api_router.include_router(behaviour.router, prefix="/behaviour", tags=["Behaviour"])

# Predictions
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])

# Analytics
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# Recommendations
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])

# Notifications
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

# Admin (protected separately)
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
