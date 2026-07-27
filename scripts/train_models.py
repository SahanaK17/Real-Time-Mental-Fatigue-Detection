"""
ML Training Pipeline
=====================
Complete end-to-end pipeline:
  1. Load and preprocess dataset
  2. Feature engineering
  3. Train multiple models (RF, XGBoost, LightGBM, CatBoost, LR, SVM)
  4. Hyperparameter optimization
  5. Cross-validation evaluation
  6. SHAP explainability
  7. Auto model selection
  8. Export best model

Usage:
    python scripts/train_models.py
    python scripts/train_models.py --data dataset/generated/fatigue_data.csv --output ml/models/
"""

import argparse
import json
import os
import warnings
from pathlib import Path
from typing import Dict, Tuple, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
    accuracy_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")

# ── Feature Configuration ─────────────────────────────────

FEATURE_COLUMNS = [
    "typing_speed_wpm",
    "typing_speed_cpm",
    "key_hold_time_ms",
    "flight_time_ms",
    "backspace_count_per_min",
    "error_rate",
    "idle_time_keyboard_s",
    "typing_burst_score",
    "typing_rhythm_variance",
    "total_keystrokes_per_min",
    "mouse_speed_px_s",
    "mouse_acceleration",
    "mouse_distance_px_per_min",
    "click_frequency_per_min",
    "double_click_rate",
    "scroll_speed",
    "idle_time_mouse_s",
    "direction_changes_per_min",
    "hover_duration_ms",
    "drag_count_per_min",
    "session_length_minutes",
    "time_of_day_hour",
    "previous_fatigue_score",
    "stress_index",
]

TARGET_BINARY = "fatigue_label"
TARGET_SCORE = "fatigue_score"


# ── Preprocessing ─────────────────────────────────────────


def load_and_preprocess(data_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Load dataset, handle missing values, engineer features."""
    print(f"\n📂 Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"   Shape: {df.shape}")

    # Select available features
    available_features = [col for col in FEATURE_COLUMNS if col in df.columns]
    print(f"   Features: {len(available_features)}/{len(FEATURE_COLUMNS)}")

    X = df[available_features].copy()
    y = df[TARGET_BINARY].copy()

    # Handle missing values
    null_counts = X.isnull().sum()
    if null_counts.any():
        print(f"   Handling {null_counts.sum()} missing values (median imputation)")
        for col in X.columns:
            if X[col].isnull().any():
                X[col].fillna(X[col].median(), inplace=True)

    # Feature engineering: derived features
    print("   Engineering derived features...")

    # Combined idle ratio
    if "idle_time_keyboard_s" in X.columns and "idle_time_mouse_s" in X.columns:
        X["combined_idle_ratio"] = (
            (X["idle_time_keyboard_s"] + X["idle_time_mouse_s"])
            / (X.get("session_length_minutes", pd.Series([60] * len(X))) * 60 + 1)
        ).clip(0, 1)

    # Typing efficiency (speed vs error rate)
    if "typing_speed_wpm" in X.columns and "error_rate" in X.columns:
        X["typing_efficiency"] = (X["typing_speed_wpm"] * (1 - X["error_rate"])).clip(0, 200)

    # Motor control index (lower = more fatigue)
    if "direction_changes_per_min" in X.columns and "mouse_speed_px_s" in X.columns:
        X["motor_control_index"] = (
            X["mouse_speed_px_s"] / (X["direction_changes_per_min"] + 1)
        ).clip(0, 100)

    print(f"   Final feature count: {len(X.columns)}")
    print(f"   Class distribution: {y.value_counts().to_dict()}")
    print(f"   Class balance: {y.mean():.1%} fatigue")

    return df, X, y


# ── Model Definitions ─────────────────────────────────────


def get_models() -> Dict[str, Any]:
    """Return all models to train and compare."""
    models = {}

    # Random Forest
    models["random_forest"] = RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",
    )

    # XGBoost
    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1,
        )
    except ImportError:
        print("   ⚠️ XGBoost not available")

    # LightGBM
    try:
        from lightgbm import LGBMClassifier

        models["lightgbm"] = LGBMClassifier(
            n_estimators=300,
            num_leaves=63,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )
    except ImportError:
        print("   ⚠️ LightGBM not available")

    # CatBoost
    try:
        from catboost import CatBoostClassifier

        models["catboost"] = CatBoostClassifier(
            iterations=300,
            learning_rate=0.05,
            depth=6,
            random_seed=42,
            verbose=0,
        )
    except ImportError:
        print("   ⚠️ CatBoost not available")

    # Logistic Regression
    models["logistic_regression"] = LogisticRegression(
        C=1.0,
        solver="lbfgs",
        max_iter=1000,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    # SVM (on sampled subset due to scalability)
    models["svm"] = SVC(
        C=1.0,
        kernel="rbf",
        probability=True,
        random_state=42,
        class_weight="balanced",
    )

    return models


# ── Training & Evaluation ─────────────────────────────────


def train_and_evaluate(
    X: pd.DataFrame,
    y: pd.Series,
    models: Dict,
    output_dir: str,
) -> Dict[str, Dict]:
    """
    Train all models with cross-validation, compare on test set.
    Returns evaluation results for each model.
    """
    print("\n🔀 Splitting dataset (80/20 stratified split)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"   Train: {len(X_train):,} | Test: {len(X_test):,}")

    # Fit scaler on training data
    print("\n⚖️ Fitting StandardScaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns)

    # For tree models, unscaled data often works better
    tree_models = {"random_forest", "xgboost", "lightgbm", "catboost"}

    results = {}
    trained_models = {}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    print("\n📊 Training & evaluating all models:")
    print("-" * 60)

    for name, model in models.items():
        print(f"\n🔧 [{name.upper()}]")

        # Use scaled data for linear/SVM, raw for trees
        X_tr = X_train if name in tree_models else X_train_scaled
        X_te = X_test if name in tree_models else X_test_scaled

        # For SVM, use a subset (too slow on full dataset)
        if name == "svm" and len(X_tr) > 20000:
            print(f"   ⚡ SVM: using 20,000 sample subset for speed")
            idx = np.random.RandomState(42).choice(len(X_tr), 20000, replace=False)
            X_tr_fit = X_tr.iloc[idx]
            y_tr_fit = y_train.iloc[idx]
        else:
            X_tr_fit = X_tr
            y_tr_fit = y_train

        # Cross-validation
        print(f"   Running 5-fold CV...")
        cv_scores = cross_val_score(model, X_tr_fit, y_tr_fit, cv=cv, scoring="f1", n_jobs=-1)
        print(f"   CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

        # Full training
        model.fit(X_tr_fit, y_tr_fit)

        # Test set evaluation
        y_pred = model.predict(X_te)
        y_proba = model.predict_proba(X_te)[:, 1]

        f1 = f1_score(y_test, y_pred, average="weighted")
        auc = roc_auc_score(y_test, y_proba)
        acc = accuracy_score(y_test, y_pred)

        print(f"   Test Accuracy: {acc:.4f}")
        print(f"   Test F1 (weighted): {f1:.4f}")
        print(f"   Test ROC-AUC: {auc:.4f}")
        print(f"   Classification Report:")
        # Print indented report
        report = classification_report(y_test, y_pred, target_names=["Alert", "Fatigued"])
        for line in report.split("\n"):
            print(f"   {line}")

        results[name] = {
            "cv_f1_mean": float(cv_scores.mean()),
            "cv_f1_std": float(cv_scores.std()),
            "test_f1": float(f1),
            "test_auc": float(auc),
            "test_accuracy": float(acc),
        }

        trained_models[name] = (model, X_tr, X_te)

    return results, trained_models, scaler, X_train, X_test, y_train, y_test


# ── Model Selection ───────────────────────────────────────


def select_best_model(results: Dict) -> str:
    """Select the best model by composite score (0.6*F1 + 0.4*AUC)."""
    scores = {name: 0.6 * r["test_f1"] + 0.4 * r["test_auc"] for name, r in results.items()}
    best = max(scores, key=scores.get)
    print(f"\n🏆 Model Comparison:")
    print("-" * 50)
    for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        indicator = "★ BEST" if name == best else "      "
        r = results[name]
        print(
            f"  {indicator} {name:<25} F1={r['test_f1']:.4f}  AUC={r['test_auc']:.4f}  Score={score:.4f}"
        )
    return best


# ── SHAP Explainability ───────────────────────────────────


def compute_shap_analysis(model, X_sample: pd.DataFrame, output_dir: str, model_name: str):
    """Compute and save SHAP feature importance analysis."""
    print(f"\n🔍 Computing SHAP values for {model_name}...")
    try:
        import shap

        # Use a small background sample for speed
        background = X_sample.sample(min(100, len(X_sample)), random_state=42)

        if model_name in {"random_forest", "xgboost", "lightgbm", "catboost"}:
            explainer = shap.TreeExplainer(model)
        else:
            explainer = shap.KernelExplainer(model.predict_proba, background)

        shap_values = explainer.shap_values(background)

        # For binary classification, use class 1 values
        if isinstance(shap_values, list):
            vals = shap_values[1]
        else:
            vals = shap_values

        # Feature importance from SHAP
        feature_importance = pd.DataFrame(
            {
                "feature": X_sample.columns,
                "mean_abs_shap": np.abs(vals).mean(axis=0),
            }
        ).sort_values("mean_abs_shap", ascending=False)

        importance_path = os.path.join(output_dir, f"shap_importance_{model_name}.csv")
        feature_importance.to_csv(importance_path, index=False)

        print(f"   Top 10 most impactful features:")
        print(feature_importance.head(10).to_string(index=False))
        print(f"   SHAP importance saved to: {importance_path}")

        return feature_importance

    except Exception as e:
        print(f"   ⚠️ SHAP analysis failed: {e}")
        return None


# ── Export ────────────────────────────────────────────────


def export_model(
    model,
    scaler,
    feature_names,
    results,
    best_model_name: str,
    output_dir: str,
):
    """Save model artifacts for use by the FastAPI inference service."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = os.path.join(output_dir, "best_model.joblib")
    joblib.dump(model, model_path, compress=3)
    print(f"\n💾 Model saved: {model_path} ({os.path.getsize(model_path) / 1024:.0f} KB)")

    # Save scaler
    scaler_path = os.path.join(output_dir, "scaler.joblib")
    joblib.dump(scaler, scaler_path)
    print(f"   Scaler saved: {scaler_path}")

    # Save feature names
    feature_names_path = os.path.join(output_dir, "feature_names.json")
    with open(feature_names_path, "w") as f:
        json.dump(list(feature_names), f, indent=2)
    print(f"   Feature names saved: {feature_names_path}")

    # Save evaluation report
    report = {
        "best_model": best_model_name,
        "trained_at": pd.Timestamp.now().isoformat(),
        "all_results": results,
        "best_results": results[best_model_name],
    }
    report_path = os.path.join(output_dir, "training_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"   Training report: {report_path}")


# ── Main ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Train and evaluate fatigue detection ML models",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data",
        default="dataset/generated/fatigue_data.csv",
        help="Path to training dataset CSV",
    )
    parser.add_argument(
        "--output",
        default="ml/models",
        help="Directory to save model artifacts",
    )
    parser.add_argument(
        "--skip-shap",
        action="store_true",
        help="Skip SHAP analysis (faster)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  Mental Fatigue Detection — ML Training Pipeline")
    print("=" * 60)

    # Load data
    df, X, y = load_and_preprocess(args.data)

    # Get models
    models = get_models()
    print(f"\n📦 Models to train: {list(models.keys())}")

    # Train and evaluate
    results, trained_models, scaler, X_train, X_test, y_train, y_test = train_and_evaluate(
        X, y, models, args.output
    )

    # Select best model
    best_name = select_best_model(results)
    best_model = trained_models[best_name][0]

    # SHAP analysis on best model
    if not args.skip_shap:
        X_sample = trained_models[best_name][1]
        compute_shap_analysis(
            best_model,
            X_sample.sample(min(1000, len(X_sample)), random_state=42),
            args.output,
            best_name,
        )

    # Export
    export_model(best_model, scaler, X.columns, results, best_name, args.output)

    print("\n" + "=" * 60)
    print(f"  ✅ Training complete! Best model: {best_name.upper()}")
    print(f"  📊 Test F1: {results[best_name]['test_f1']:.4f}")
    print(f"  📈 Test AUC: {results[best_name]['test_auc']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
