"""
Database Models — Complete Schema
==================================
Normalized PostgreSQL schema with all entities:
  - User (with roles)
  - TrackerSession
  - BehaviourSnapshot
  - FatiguePrediction
  - Recommendation
  - Notification
  - AuditLog
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Index,
    types,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class UUID(types.TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL's UUID type when using PostgreSQL,
    and CHAR(36) for SQLite and other databases.
    """

    impl = types.CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID

            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(types.CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


from app.db.base import Base

# ── Enums ──────────────────────────────────────────────────


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"
    RESEARCHER = "researcher"


class FatigueLevel(str, enum.Enum):
    ALERT = "alert"
    MILD = "mild"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"


class NotificationType(str, enum.Enum):
    FATIGUE_ALERT = "fatigue_alert"
    HIGH_RISK = "high_risk"
    BREAK_REMINDER = "break_reminder"
    DAILY_SUMMARY = "daily_summary"
    SYSTEM = "system"


class NotificationChannel(str, enum.Enum):
    BROWSER = "browser"
    EMAIL = "email"
    IN_APP = "in_app"


# ── Mixins ─────────────────────────────────────────────────


class UUIDMixin:
    """UUID primary key mixin."""

    id = Column(
        UUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class TimestampMixin:
    """Automatic created_at/updated_at timestamps."""

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── Models ─────────────────────────────────────────────────


class User(Base, UUIDMixin, TimestampMixin):
    """
    User account with role-based access control.
    Employees are tracked, Admins have full access, Researchers read analytics.
    """

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE, nullable=False)
    department = Column(String(100), nullable=True)
    job_title = Column(String(150), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Preferences
    notification_preferences = Column(JSON, default=dict, nullable=False)
    fatigue_threshold = Column(Float, default=0.7, nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)

    # Relationships
    tracker_sessions = relationship(
        "TrackerSession", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"


class TrackerSession(Base, UUIDMixin, TimestampMixin):
    """
    A continuous monitoring session started by the desktop tracker.
    Corresponds to one work session (e.g., one day's computer usage).
    """

    __tablename__ = "tracker_sessions"

    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Session metadata
    hostname = Column(String(255), nullable=True)
    os_platform = Column(String(100), nullable=True)
    tracker_version = Column(String(20), nullable=True)

    # Aggregate statistics (computed at session end)
    total_keystrokes = Column(BigInteger, default=0)
    total_mouse_distance = Column(Float, default=0.0)
    total_clicks = Column(Integer, default=0)
    avg_fatigue_score = Column(Float, nullable=True)
    max_fatigue_score = Column(Float, nullable=True)
    peak_fatigue_time = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="tracker_sessions")
    behaviour_snapshots = relationship(
        "BehaviourSnapshot", back_populates="session", cascade="all, delete-orphan"
    )
    predictions = relationship(
        "FatiguePrediction", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_tracker_sessions_user_started", "user_id", "started_at"),)

    def __repr__(self) -> str:
        return f"<TrackerSession {self.id} [{self.status}]>"


class BehaviourSnapshot(Base, UUIDMixin):
    """
    A 1-second window of aggregated keyboard + mouse behavioral metrics.
    This is the raw input to the ML model.
    """

    __tablename__ = "behaviour_snapshots"

    session_id = Column(
        UUID(), ForeignKey("tracker_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    captured_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # ── Keyboard Metrics ─────────────────────────────────
    typing_speed_wpm = Column(Float, nullable=True)  # Words per minute
    typing_speed_cpm = Column(Float, nullable=True)  # Characters per minute
    key_hold_time_ms = Column(Float, nullable=True)  # Average key dwell time
    flight_time_ms = Column(Float, nullable=True)  # Average inter-key interval
    backspace_count = Column(Integer, default=0)  # Backspaces in window
    error_rate = Column(Float, default=0.0)  # Backspaces / total keystrokes
    idle_time_keyboard_s = Column(Float, default=0.0)  # Seconds without keypress
    typing_burst_score = Column(Float, nullable=True)  # Burstiness metric
    typing_rhythm_variance = Column(Float, nullable=True)  # Inter-key variance
    total_keystrokes = Column(Integer, default=0)

    # ── Mouse Metrics ────────────────────────────────────
    mouse_speed_px_s = Column(Float, nullable=True)  # Average cursor speed
    mouse_acceleration = Column(Float, nullable=True)  # Speed change rate
    mouse_distance_px = Column(Float, default=0.0)  # Total distance moved
    click_frequency = Column(Float, default=0.0)  # Clicks per second
    double_click_count = Column(Integer, default=0)
    drag_count = Column(Integer, default=0)
    scroll_speed = Column(Float, default=0.0)
    scroll_distance = Column(Float, default=0.0)
    idle_time_mouse_s = Column(Float, default=0.0)  # Seconds without movement
    direction_changes = Column(Integer, default=0)  # Mouse trajectory jitter
    hover_duration_ms = Column(Float, default=0.0)  # Average hover time

    # ── Combined Metrics ─────────────────────────────────
    total_idle_time_s = Column(Float, default=0.0)  # Combined idle
    session_elapsed_s = Column(Integer, default=0)  # Seconds since session start
    time_of_day_hour = Column(Float, nullable=True)  # Decimal hour (0-24)

    # Relationship
    session = relationship("TrackerSession", back_populates="behaviour_snapshots")

    __table_args__ = (
        Index("ix_behaviour_snapshots_session_time", "session_id", "captured_at"),
        Index("ix_behaviour_snapshots_user_time", "user_id", "captured_at"),
    )

    def __repr__(self) -> str:
        return f"<BehaviourSnapshot {self.id} speed={self.typing_speed_wpm}wpm>"


class FatiguePrediction(Base, UUIDMixin):
    """
    ML model prediction output for a behaviour snapshot.
    Includes SHAP explainability values and recommendations.
    """

    __tablename__ = "fatigue_predictions"

    session_id = Column(
        UUID(), ForeignKey("tracker_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_id = Column(
        UUID(), ForeignKey("behaviour_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    predicted_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Prediction outputs
    fatigue_score = Column(Float, nullable=False)  # 0.0 - 1.0
    fatigue_level = Column(Enum(FatigueLevel), nullable=False)
    confidence = Column(Float, nullable=False)  # Model confidence
    model_name = Column(String(100), nullable=False)  # e.g., "xgboost"
    model_version = Column(String(20), nullable=True)

    # Explainability
    shap_values = Column(JSON, nullable=True)  # {feature: shap_value}
    top_features = Column(JSON, nullable=True)  # Top 5 contributing features
    feature_values = Column(JSON, nullable=True)  # Raw feature values used

    # Explanation text
    explanation_text = Column(Text, nullable=True)
    recommendations_generated = Column(Boolean, default=False)

    # Relationships
    session = relationship("TrackerSession", back_populates="predictions")
    recommendation = relationship("Recommendation", back_populates="prediction", uselist=False)

    __table_args__ = (Index("ix_fatigue_predictions_user_time", "user_id", "predicted_at"),)

    def __repr__(self) -> str:
        return f"<FatiguePrediction score={self.fatigue_score:.2f} level={self.fatigue_level}>"


class Recommendation(Base, UUIDMixin, TimestampMixin):
    """
    Smart wellness recommendation triggered by a fatigue prediction.
    """

    __tablename__ = "recommendations"

    prediction_id = Column(
        UUID(),
        ForeignKey("fatigue_predictions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # e.g., "break", "exercise", "hydration"
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high
    duration_minutes = Column(Integer, nullable=True)  # Suggested activity duration
    icon = Column(String(50), nullable=True)  # Emoji or icon code
    action_url = Column(String(500), nullable=True)  # Optional deep link

    is_dismissed = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    prediction = relationship("FatiguePrediction", back_populates="recommendation")

    def __repr__(self) -> str:
        return f"<Recommendation {self.category}: {self.title}>"


class Notification(Base, UUIDMixin, TimestampMixin):
    """
    Notification sent to a user via various channels.
    """

    __tablename__ = "notifications"

    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)

    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Extra payload (e.g., fatigue score)

    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    __table_args__ = (Index("ix_notifications_user_read", "user_id", "is_read"),)

    def __repr__(self) -> str:
        return f"<Notification {self.type} -> {self.user_id}>"


class AuditLog(Base, UUIDMixin):
    """
    Immutable audit trail for compliance and security monitoring.
    """

    __tablename__ = "audit_logs"

    user_id = Column(UUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # e.g., "login", "logout", "export_data"
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # Supports IPv6
    user_agent = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    success = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_time", "user_id", "timestamp"),
        Index("ix_audit_logs_action_time", "action", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id}>"
