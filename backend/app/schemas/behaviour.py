"""
Pydantic Schemas — Behaviour Snapshots
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BehaviourSnapshotCreate(BaseModel):
    session_id: UUID
    captured_at: Optional[datetime] = None

    # Keyboard
    typing_speed_wpm: Optional[float] = Field(default=None, ge=0, le=500)
    typing_speed_cpm: Optional[float] = Field(default=None, ge=0, le=3000)
    key_hold_time_ms: Optional[float] = Field(default=None, ge=0, le=5000)
    flight_time_ms: Optional[float] = Field(default=None, ge=0, le=10000)
    backspace_count: int = Field(default=0, ge=0)
    error_rate: float = Field(default=0.0, ge=0, le=1)
    idle_time_keyboard_s: float = Field(default=0.0, ge=0)
    typing_burst_score: Optional[float] = Field(default=None, ge=0)
    typing_rhythm_variance: Optional[float] = Field(default=None, ge=0)
    total_keystrokes: int = Field(default=0, ge=0)

    # Mouse
    mouse_speed_px_s: Optional[float] = Field(default=None, ge=0)
    mouse_acceleration: Optional[float] = None
    mouse_distance_px: float = Field(default=0.0, ge=0)
    click_frequency: float = Field(default=0.0, ge=0)
    double_click_count: int = Field(default=0, ge=0)
    drag_count: int = Field(default=0, ge=0)
    scroll_speed: float = Field(default=0.0, ge=0)
    scroll_distance: float = Field(default=0.0, ge=0)
    idle_time_mouse_s: float = Field(default=0.0, ge=0)
    direction_changes: int = Field(default=0, ge=0)
    hover_duration_ms: float = Field(default=0.0, ge=0)

    # Combined
    total_idle_time_s: float = Field(default=0.0, ge=0)
    session_elapsed_s: int = Field(default=0, ge=0)
    time_of_day_hour: Optional[float] = Field(default=None, ge=0, le=24)

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "typing_speed_wpm": 65.5,
                "key_hold_time_ms": 85.3,
                "flight_time_ms": 120.7,
                "backspace_count": 2,
                "error_rate": 0.05,
                "mouse_speed_px_s": 450.2,
                "mouse_distance_px": 892.5,
                "click_frequency": 0.8,
                "session_elapsed_s": 3600,
                "time_of_day_hour": 14.5,
            }
        }
    }


class BehaviourSnapshotResponse(BaseModel):
    id: str
    session_id: str
    user_id: str
    captured_at: datetime
    typing_speed_wpm: Optional[float]
    key_hold_time_ms: Optional[float]
    flight_time_ms: Optional[float]
    error_rate: float
    mouse_speed_px_s: Optional[float]
    mouse_distance_px: float
    click_frequency: float
    total_idle_time_s: float

    model_config = {"from_attributes": True}

    from pydantic import field_validator

    @field_validator("id", "session_id", "user_id", mode="before")
    @classmethod
    def serialize_uuid(cls, v) -> str:
        return str(v)
