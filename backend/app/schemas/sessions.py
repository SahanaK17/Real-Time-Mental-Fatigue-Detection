"""
Pydantic Schemas — Sessions
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.db.models import SessionStatus


class SessionCreate(BaseModel):
    hostname: Optional[str] = Field(default=None, max_length=255)
    os_platform: Optional[str] = Field(default=None, max_length=100)
    tracker_version: Optional[str] = Field(default=None, max_length=20)


class SessionResponse(BaseModel):
    id: str
    user_id: str
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    hostname: Optional[str] = None
    os_platform: Optional[str] = None
    tracker_version: Optional[str] = None
    total_keystrokes: Optional[int] = None
    total_mouse_distance: Optional[float] = None
    avg_fatigue_score: Optional[float] = None
    max_fatigue_score: Optional[float] = None

    model_config = {"from_attributes": True}

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def serialize_uuid(cls, v) -> str:
        return str(v)


class SessionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    sessions: List[SessionResponse]
