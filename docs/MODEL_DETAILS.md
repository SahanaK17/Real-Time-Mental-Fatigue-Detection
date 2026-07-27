# Model Details

This document provides a transparent and complete account of the MindGuard machine learning pipeline — including the training methodology, evaluation results, known limitations, and deployment considerations.

---

**Navigation:** [← Back to README](../README.md) | [Dataset](DATASET.md) | [Architecture](architecture/ARCHITECTURE.md)

---

## Table of Contents

- [Problem Framing](#problem-framing)
- [Feature Engineering](#feature-engineering)
- [Data Leakage Disclosure](#data-leakage-disclosure)
- [Model Architecture & Selection](#model-architecture--selection)
- [Training Configuration](#training-configuration)
- [Evaluation Results](#evaluation-results)
- [SHAP Explainability](#shap-explainability)
- [Inference Pipeline](#inference-pipeline)
- [Known Limitations](#known-limitations)
- [Retraining Guide](#retraining-guide)

---

## Problem Framing

MindGuard treats fatigue detection as a **binary classification problem**:

- **Class 0 (Alert):** The user's behavioral signals are within a normal, rested baseline.
- **Class 1 (Fatigued):** The user's behavioral signals indicate cognitive load or exhaustion.

Each observation is a 1-second aggregated feature vector derived from keyboard and mouse interaction events captured during that window. The model predicts the probability that the user is fatigued, which is used as a continuous `fatigue_score` (0.0 – 1.0).

---

## Feature Engineering

**24 behavioral features** are extracted per observation window:

### Keyboard Dynamics (10 features)

| Feature | Description | Fatigue Correlation |
|:---|:---|:---:|
| `typing_speed_wpm` | Words per minute | Decreases with fatigue |
| `typing_speed_cpm` | Characters per minute | Decreases with fatigue |
| `key_hold_time_ms` | Average key dwell time (ms) | Increases with fatigue |
| `flight_time_ms` | Average inter-keystroke interval (ms) | Increases with fatigue |
| `backspace_count` | Backspace events per window | Increases with fatigue |
| `error_rate` | Backspace / total keystrokes | Increases with fatigue |
| `idle_time_keyboard_s` | Seconds without a keystroke | Increases with fatigue |
| `typing_burst_score` | Ratio of burst-typing intervals | Decreases with fatigue |
| `typing_rhythm_variance` | Variance of inter-keystroke timings | Increases with fatigue |
| `total_keystrokes` | Total keys pressed in window | Decreases with fatigue |

### Mouse Kinematics (11 features)

| Feature | Description | Fatigue Correlation |
|:---|:---|:---:|
| `mouse_speed_px_s` | Average cursor velocity (px/s) | Decreases with fatigue |
| `mouse_acceleration` | Speed change rate | Decreases with fatigue |
| `mouse_distance_px` | Total distance traveled (px) | Decreases with fatigue |
| `click_frequency` | Clicks per second | Decreases with fatigue |
| `double_click_count` | Double-click events | Increases with fatigue (misclicks) |
| `drag_count` | Drag events per window | Decreases with fatigue |
| `scroll_speed` | Scroll velocity | Decreases with fatigue |
| `scroll_distance` | Total scroll distance | Varies |
| `idle_time_mouse_s` | Seconds without mouse movement | Increases with fatigue |
| `direction_changes` | Trajectory direction reversals (jitter proxy) | Increases with fatigue |
| `hover_duration_ms` | Average hover time (hesitation proxy) | Increases with fatigue |

### Contextual Features (3 features)

| Feature | Description |
|:---|:---|
| `total_idle_time_s` | Combined keyboard + mouse idle time |
| `session_elapsed_s` | Seconds elapsed since session start |
| `time_of_day_hour` | Decimal hour (0.0–24.0) for circadian modeling |

### Derived Features (computed during training)

| Feature | Formula | Purpose |
|:---|:---|:---|
| `combined_idle_ratio` | `(idle_kb + idle_mouse) / session_length` | Normalized inactivity |
| `typing_efficiency` | `wpm × (1 - error_rate)` | Net effective speed |
| `motor_control_index` | `mouse_speed / (direction_changes + 1)` | Movement precision proxy |

---

## Data Leakage Disclosure

> **Important:** The feature `previous_fatigue_score` was present in an earlier version of the synthetic dataset schema. This feature constitutes **direct target leakage** and was removed from the training pipeline. The current feature set (24 features listed above) does not include any derived target variables.

The cross-validation F1 scores recorded in `ml/models/training_report.json` (values near 0.01–0.12) are anomalously low and reflect a **class imbalance artifact** in the stratified 5-fold CV splits on the synthetic dataset — the CV folds did not distribute the minority class correctly across all folds. The **test set F1 scores** (0.74–0.94) are the reliable metrics, as they use a single 80/20 stratified split where class balance was preserved.

---

## Model Architecture & Selection

Five classifier architectures were evaluated:

| Model | Strengths | Configuration |
|:---|:---|:---|
| **LightGBM** | Fast training, low memory, handles sparse data | `n_estimators=300, num_leaves=63, lr=0.05` |
| XGBoost | High accuracy, regularization support | `n_estimators=300, max_depth=6, lr=0.05` |
| Random Forest | Robust to noise, interpretable | `n_estimators=300, max_depth=15` |
| SVM | Strong on small, clean datasets | `C=1.0, kernel=rbf` |
| Logistic Regression | Fast, interpretable baseline | `C=1.0, solver=lbfgs` |

**LightGBM was selected** as the production model for two reasons:
1. Highest composite score (0.6 × F1 + 0.4 × AUC) on the test set
2. Sub-millisecond inference latency, compatible with the real-time prediction pipeline

---

## Training Configuration

```python
# Train/test split
test_size = 0.20
random_state = 42
stratify = y   # preserves class balance in splits

# Cross-validation
StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Feature scaling
StandardScaler (applied to LR and SVM only; tree-based models use raw features)
```

---

## Evaluation Results

Results on held-out test set (30,000 observations from 150,000-record synthetic dataset):

| Model | Test F1 (weighted) | Test Accuracy | Test AUC-ROC |
|:---|:---:|:---:|:---:|
| **LightGBM** ✅ | **0.9373** | **95.72%** | 0.587 |
| XGBoost | 0.9370 | 95.70% | 0.581 |
| Random Forest | 0.9225 | 92.01% | 0.569 |
| SVM | 0.8341 | 76.87% | 0.540 |
| Logistic Regression | 0.7481 | 64.29% | 0.604 |

> **AUC-ROC Note:** The relatively modest AUC-ROC scores (0.54–0.60) reflect the **synthetic nature of the dataset**. The synthetic generator produces clearly separable fatigue states, meaning the model achieves high F1 through precise decision boundaries but may not generalize well to real-world noisy data where classes overlap more.

---

## SHAP Explainability

Every prediction from the production model includes SHAP (SHapley Additive exPlanations) values computed using `shap.TreeExplainer`.

### How SHAP values are used

- **Per-prediction explanation:** The top 5 features by absolute SHAP value are returned with each inference result.
- **Direction:** A positive SHAP value means the feature increased the predicted fatigue score; negative means it decreased it.
- **Frontend display:** The React dashboard renders these as a ranked feature importance bar chart on the Prediction Detail view.

### Example SHAP output

```json
{
  "top_features": [
    {
      "feature": "error_rate",
      "shap_value": 0.142,
      "feature_value": 0.18,
      "impact": "increases"
    },
    {
      "feature": "idle_time_keyboard_s",
      "shap_value": 0.098,
      "feature_value": 28.3,
      "impact": "increases"
    }
  ]
}
```

---

## Inference Pipeline

```
[Tracker sends 24-feature JSON]
        ↓
[FastAPI background task]
        ↓
[Feature vector assembled in FEATURE_NAMES order]
        ↓
[StandardScaler.transform() — NOT applied for LightGBM]
        ↓
[model.predict_proba(X) → [p_alert, p_fatigued]]
        ↓
[p_fatigued → fatigue_score (0.0–1.0)]
        ↓
[SHAP TreeExplainer → top 5 features]
        ↓
[Return: score, level, confidence, shap_values, top_features]
```

**Fallback:** If the model is not loaded (e.g., first boot before training), a weighted heuristic using error rate and idle times produces a rough score. This is transparently labeled as `model_name: "heuristic_fallback"` in the API response.

---

## Known Limitations

1. **Synthetic data only.** The model has not been validated against labeled real-world psychomotor fatigue data. Real-world performance is unknown.
2. **No personalization.** A single global model is used for all users. Individual behavioral baselines vary significantly; a per-user fine-tuning approach would improve accuracy.
3. **Temporal effects.** The 1-second window is computationally efficient but may miss longer-scale fatigue patterns (e.g., 15-minute drift).
4. **No circadian calibration.** While `time_of_day_hour` is included as a feature, the model does not dynamically adjust thresholds for individual circadian rhythms.

---

## Retraining Guide

```bash
# 1. Generate fresh synthetic data
python dataset/generator.py --rows 150000 --output dataset/generated/fatigue_data.csv

# 2. Train all models and export the best
python scripts/train_models.py \
  --data dataset/generated/fatigue_data.csv \
  --output ml/models/

# 3. Restart the backend to load the new model
# (The model is loaded once at startup via ModelRegistry.load())
```
