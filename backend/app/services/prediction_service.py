"""
Prediction Service
===================
Orchestrates ML inference, saves predictions to DB,
triggers recommendations, and sends notifications.
"""

import asyncio
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    BehaviourSnapshot,
    FatiguePrediction,
    FatigueLevel,
    Recommendation,
    TrackerSession,
    User,
)
from app.ml.inference import model_registry

logger = structlog.get_logger(__name__)


class PredictionService:
    """Orchestrates the complete prediction pipeline."""

    async def predict_and_save(
        self,
        snapshot: BehaviourSnapshot,
        user: User,
        session: TrackerSession,
        db: AsyncSession,
    ) -> Optional[FatiguePrediction]:
        """
        Run inference on a behaviour snapshot, persist results,
        and optionally generate recommendations.
        """
        # Build feature dict from snapshot
        features = self._extract_features(snapshot)

        # Run inference in thread pool (blocking scikit-learn call)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, model_registry.predict, features)

        if not result:
            return None

        # Determine fatigue level enum
        fatigue_level = FatigueLevel(result["fatigue_level"])

        # Save prediction
        prediction = FatiguePrediction(
            session_id=session.id,
            user_id=user.id,
            snapshot_id=snapshot.id,
            fatigue_score=result["fatigue_score"],
            fatigue_level=fatigue_level,
            confidence=result["confidence"],
            model_name=result["model_name"],
            model_version=result.get("model_version", "1.0.0"),
            shap_values=result.get("shap_values"),
            top_features=result.get("top_features"),
            feature_values=result.get("feature_values"),
            explanation_text=self._generate_explanation(result),
        )
        db.add(prediction)
        await db.flush()

        # Generate recommendation if fatigue is elevated
        if result["fatigue_score"] >= user.fatigue_threshold:
            recommendation = self._generate_recommendation(prediction, result)
            if recommendation:
                prediction.recommendations_generated = True
                db.add(recommendation)

        # Check if high-risk notification should be sent
        if result["fatigue_score"] >= 0.85:
            await self._trigger_high_risk_notification(user, result, db)

        return prediction

    def _extract_features(self, snapshot: BehaviourSnapshot) -> dict:
        """Convert ORM model fields to feature dict for inference."""
        return {
            "typing_speed_wpm": snapshot.typing_speed_wpm,
            "typing_speed_cpm": snapshot.typing_speed_cpm,
            "key_hold_time_ms": snapshot.key_hold_time_ms,
            "flight_time_ms": snapshot.flight_time_ms,
            "backspace_count": snapshot.backspace_count,
            "error_rate": snapshot.error_rate,
            "idle_time_keyboard_s": snapshot.idle_time_keyboard_s,
            "typing_burst_score": snapshot.typing_burst_score,
            "typing_rhythm_variance": snapshot.typing_rhythm_variance,
            "total_keystrokes": snapshot.total_keystrokes,
            "mouse_speed_px_s": snapshot.mouse_speed_px_s,
            "mouse_acceleration": snapshot.mouse_acceleration,
            "mouse_distance_px": snapshot.mouse_distance_px,
            "click_frequency": snapshot.click_frequency,
            "double_click_count": snapshot.double_click_count,
            "drag_count": snapshot.drag_count,
            "scroll_speed": snapshot.scroll_speed,
            "scroll_distance": snapshot.scroll_distance,
            "idle_time_mouse_s": snapshot.idle_time_mouse_s,
            "direction_changes": snapshot.direction_changes,
            "hover_duration_ms": snapshot.hover_duration_ms,
            "total_idle_time_s": snapshot.total_idle_time_s,
            "session_elapsed_s": snapshot.session_elapsed_s,
            "time_of_day_hour": snapshot.time_of_day_hour,
        }

    def _generate_explanation(self, result: dict) -> str:
        """Generate human-readable explanation of the prediction."""
        score = result["fatigue_score"]
        level = result["fatigue_level"]
        top_features = result.get("top_features", [])

        explanation_parts = [f"Fatigue level detected as {level.upper()} (score: {score:.0%})."]

        if top_features:
            explanation_parts.append("Primary contributing factors:")
            for feat in top_features[:3]:
                name = feat["feature"].replace("_", " ").title()
                impact = feat["impact"]
                val = feat["feature_value"]
                explanation_parts.append(f"  • {name}: {val:.2f} ({impact} fatigue)")

        return " ".join(explanation_parts)

    def _generate_recommendation(
        self, prediction: FatiguePrediction, result: dict
    ) -> Optional[Recommendation]:
        """Select the most appropriate recommendation based on fatigue level and top features."""
        score = result["fatigue_score"]
        top_features = result.get("top_features", [])
        top_feature_names = [f["feature"] for f in top_features[:2]]

        # Recommendation catalog
        recommendations = {
            "high_idle": {
                "title": "Take a Short Walk",
                "description": "You've been idle for an extended period. A 5-minute walk will boost circulation and refresh your focus.",
                "category": "movement",
                "duration_minutes": 5,
                "icon": "🚶",
                "priority": 2,
            },
            "high_error_rate": {
                "title": "Proofreading Break",
                "description": "Your error rate has increased significantly. Take 3 minutes to review your recent work before continuing.",
                "category": "break",
                "duration_minutes": 3,
                "icon": "📝",
                "priority": 2,
            },
            "high_fatigue_generic": {
                "title": "Pomodoro Break — You've Earned It!",
                "description": "Mental fatigue detected. Take a 5-minute break: stretch, hydrate, and practice deep breathing.",
                "category": "pomodoro",
                "duration_minutes": 5,
                "icon": "🍅",
                "priority": 3,
            },
            "critical_fatigue": {
                "title": "⚠️ Critical Fatigue — Extended Break Required",
                "description": "Your fatigue level is critically high. Take a 15-minute break immediately. Drink water, step away from the screen, and do light stretching.",
                "category": "break",
                "duration_minutes": 15,
                "icon": "🔴",
                "priority": 3,
            },
            "eye_exercise": {
                "title": "Eye Exercise (20-20-20 Rule)",
                "description": "Look at an object 20 feet away for 20 seconds. Repeat 3 times to reduce eye strain.",
                "category": "eye_exercise",
                "duration_minutes": 2,
                "icon": "👁️",
                "priority": 1,
            },
        }

        # Select recommendation based on context
        if score >= 0.85:
            key = "critical_fatigue"
        elif (
            "idle_time_keyboard_s" in top_feature_names or "idle_time_mouse_s" in top_feature_names
        ):
            key = "high_idle"
        elif "error_rate" in top_feature_names:
            key = "high_error_rate"
        else:
            key = "high_fatigue_generic"

        rec_data = recommendations[key]

        return Recommendation(
            prediction_id=prediction.id,
            user_id=prediction.user_id,
            **rec_data,
        )

    async def _trigger_high_risk_notification(
        self, user: User, result: dict, db: AsyncSession
    ) -> None:
        """Create a high-risk notification for admin review."""
        from app.db.models import Notification, NotificationType, NotificationChannel
        from datetime import datetime, timezone

        notification = Notification(
            user_id=user.id,
            type=NotificationType.HIGH_RISK,
            channel=NotificationChannel.IN_APP,
            title="⚠️ High Fatigue Alert",
            body=f"Critical fatigue detected (score: {result['fatigue_score']:.0%}). Immediate break recommended.",
            data={"fatigue_score": result["fatigue_score"], "level": result["fatigue_level"]},
        )
        db.add(notification)
        logger.warning(
            "High risk fatigue detected", user_id=str(user.id), score=result["fatigue_score"]
        )
