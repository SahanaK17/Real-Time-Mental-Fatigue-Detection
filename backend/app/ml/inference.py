"""
ML Inference Service
=====================
Loads trained model from disk and provides thread-safe prediction
with SHAP explainability. Sub-10ms inference latency.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import structlog

logger = structlog.get_logger(__name__)

# Feature names in exact order expected by the model
FEATURE_NAMES = [
    "typing_speed_wpm",
    "typing_speed_cpm",
    "key_hold_time_ms",
    "flight_time_ms",
    "backspace_count",
    "error_rate",
    "idle_time_keyboard_s",
    "typing_burst_score",
    "typing_rhythm_variance",
    "total_keystrokes",
    "mouse_speed_px_s",
    "mouse_acceleration",
    "mouse_distance_px",
    "click_frequency",
    "double_click_count",
    "drag_count",
    "scroll_speed",
    "scroll_distance",
    "idle_time_mouse_s",
    "direction_changes",
    "hover_duration_ms",
    "total_idle_time_s",
    "session_elapsed_s",
    "time_of_day_hour",
]

FATIGUE_LEVEL_MAP = {
    (0.0, 0.25): "alert",
    (0.25, 0.50): "mild",
    (0.50, 0.70): "moderate",
    (0.70, 0.85): "high",
    (0.85, 1.01): "critical",
}


def score_to_level(score: float) -> str:
    """Convert a 0-1 fatigue score to a categorical level."""
    for (low, high), level in FATIGUE_LEVEL_MAP.items():
        if low <= score < high:
            return level
    return "critical"


class ModelRegistry:
    """
    Thread-safe ML model registry.
    Loads model once at startup; provides synchronous predict method
    called from async route handlers via run_in_executor.
    """

    def __init__(self):
        self._model = None
        self._scaler = None
        self._explainer = None
        self._feature_names: List[str] = FEATURE_NAMES
        self._model_name: str = "unknown"
        self._model_version: str = "1.0.0"
        self.is_loaded: bool = False

    async def load(self) -> None:
        """Load model artifacts from disk."""
        from app.core.config import settings
        import joblib

        model_path = Path(settings.ML_MODEL_PATH)
        scaler_path = Path(settings.ML_SCALER_PATH)

        if not model_path.exists():
            logger.warning("Model file not found", path=str(model_path))
            return

        # Load in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        self._model, self._scaler = await loop.run_in_executor(
            None, self._load_artifacts, str(model_path), str(scaler_path)
        )

        # Load feature names if available
        feature_path = Path(settings.ML_FEATURE_NAMES_PATH)
        if feature_path.exists():
            with open(feature_path) as f:
                self._feature_names = json.load(f)

        # Determine model name from filename
        self._model_name = model_path.stem.replace("best_model_", "")

        # Initialize SHAP explainer
        try:
            import shap

            self._explainer = shap.TreeExplainer(self._model)
            logger.info("SHAP explainer initialized")
        except Exception as e:
            logger.warning("SHAP not available for this model type", error=str(e))

        self.is_loaded = True
        logger.info("ML model loaded", model=self._model_name, features=len(self._feature_names))

    @staticmethod
    def _load_artifacts(model_path: str, scaler_path: str):
        import joblib

        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
        return model, scaler

    def predict(self, features: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Run synchronous inference. Returns prediction dict or None.

        Args:
            features: Dict mapping feature names to values

        Returns:
            {
                "fatigue_score": float,
                "fatigue_level": str,
                "confidence": float,
                "model_name": str,
                "shap_values": dict,
                "top_features": list,
                "feature_values": dict,
            }
        """
        if not self.is_loaded or self._model is None:
            return self._fallback_prediction(features)

        try:
            # Build feature vector in correct order
            X = np.array([[features.get(name, 0.0) or 0.0 for name in self._feature_names]])

            # Scale features if scaler is available
            if self._scaler is not None:
                X = self._scaler.transform(X)

            # Predict probability
            proba = self._model.predict_proba(X)[0]
            # proba[1] = probability of fatigue class (label=1)
            fatigue_score = float(proba[1]) if len(proba) > 1 else float(proba[0])
            confidence = float(max(proba))

            # Compute SHAP values
            shap_values = {}
            top_features = []

            if self._explainer is not None:
                try:
                    shap_vals = self._explainer.shap_values(X)
                    # For binary classification, use class 1 SHAP values
                    if isinstance(shap_vals, list):
                        vals = shap_vals[1][0]
                    else:
                        vals = shap_vals[0]

                    shap_values = {
                        name: round(float(val), 6) for name, val in zip(self._feature_names, vals)
                    }

                    # Top 5 most impactful features (by abs SHAP value)
                    sorted_features = sorted(
                        shap_values.items(), key=lambda x: abs(x[1]), reverse=True
                    )[:5]
                    top_features = [
                        {
                            "feature": name,
                            "shap_value": val,
                            "feature_value": round(features.get(name, 0.0) or 0.0, 4),
                            "impact": "increases" if val > 0 else "decreases",
                        }
                        for name, val in sorted_features
                    ]
                except Exception as e:
                    logger.warning("SHAP computation failed", error=str(e))

            return {
                "fatigue_score": round(fatigue_score, 4),
                "fatigue_level": score_to_level(fatigue_score),
                "confidence": round(confidence, 4),
                "model_name": self._model_name,
                "model_version": self._model_version,
                "shap_values": shap_values,
                "top_features": top_features,
                "feature_values": {k: round(v or 0.0, 4) for k, v in features.items()},
            }

        except Exception as e:
            logger.error("Inference error", error=str(e))
            return self._fallback_prediction(features)

    def _fallback_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Rule-based fallback when ML model is not loaded.
        Uses heuristic scoring from key behavioral signals.
        """
        score = 0.0
        weights = {
            "error_rate": 0.25,
            "idle_time_keyboard_s": 0.20,
            "idle_time_mouse_s": 0.15,
            "typing_rhythm_variance": 0.15,
            "key_hold_time_ms": 0.10,
            "direction_changes": 0.15,
        }

        # Normalize and weight each signal
        error_rate = min(features.get("error_rate", 0) or 0, 1.0)
        score += error_rate * weights["error_rate"]

        idle_kb = min((features.get("idle_time_keyboard_s", 0) or 0) / 60, 1.0)
        score += idle_kb * weights["idle_time_keyboard_s"]

        idle_m = min((features.get("idle_time_mouse_s", 0) or 0) / 60, 1.0)
        score += idle_m * weights["idle_time_mouse_s"]

        # Cap at 0.95 for fallback
        fatigue_score = min(score, 0.95)

        return {
            "fatigue_score": round(fatigue_score, 4),
            "fatigue_level": score_to_level(fatigue_score),
            "confidence": 0.5,
            "model_name": "heuristic_fallback",
            "model_version": "1.0.0",
            "shap_values": {},
            "top_features": [],
            "feature_values": features,
        }


# Singleton
model_registry = ModelRegistry()
