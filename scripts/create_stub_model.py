"""
Create a minimal stub model for development (no training needed).
Saves a scikit-learn Random Forest with random weights.
The backend will use this until a real model is trained.

Usage:
    python scripts/create_stub_model.py
"""

import json
import os
import sys

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

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

output_dir = os.path.join(os.path.dirname(__file__), "..", "ml", "models")
os.makedirs(output_dir, exist_ok=True)

n_features = len(FEATURE_NAMES)
np.random.seed(42)

# Generate small random training set
X = np.random.randn(200, n_features)
y = (X[:, 5] > 0).astype(int)  # error_rate drives label

# Scaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Model
model = RandomForestClassifier(n_estimators=10, max_depth=4, random_state=42)
model.fit(X_scaled, y)

# Save
joblib.dump(model, os.path.join(output_dir, "best_model.joblib"))
joblib.dump(scaler, os.path.join(output_dir, "scaler.joblib"))

with open(os.path.join(output_dir, "feature_names.json"), "w") as f:
    json.dump(FEATURE_NAMES, f, indent=2)

report = {
    "model_name": "stub_random_forest",
    "model_version": "0.0.1-stub",
    "note": "Stub model for development. Run scripts/train_models.py for production.",
    "features": FEATURE_NAMES,
    "n_estimators": 10,
}

with open(os.path.join(output_dir, "training_report.json"), "w") as f:
    json.dump(report, f, indent=2)

print("[OK] Stub model created at ml/models/")
print(f"     Features: {len(FEATURE_NAMES)}")
print("     NOTE: Run 'python scripts/train_models.py' for a real production model")
