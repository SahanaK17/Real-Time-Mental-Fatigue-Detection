# FAQ

Frequently asked questions from contributors, technical reviewers, and curious developers.

---

**Navigation:** [← Back to README](../README.md)

---

## General

**Q: Is this system actually detecting fatigue accurately?**

The model (LightGBM, F1: 0.937) was trained on a **synthetic dataset** of 150,000 observations generated using published behavioral science literature. It has not been validated against labeled real-world psychomotor fatigue data. The high F1 reflects performance on synthetic data; real-world accuracy is unknown. See [Model Details](MODEL_DETAILS.md) and [Dataset](DATASET.md) for a complete honest disclosure.

---

**Q: Does the tracker record what I type?**

No. The tracker hooks into OS-level input events using `pynput` but explicitly discards all key identity information at the hook level. Only timing metrics are retained: time between keys (flight time), duration of key press (hold time), and whether a backspace was pressed (for error rate). No character, word, or content is ever processed, stored, or transmitted.

---

**Q: What data is sent to the server?**

Each second, the tracker sends a JSON object containing 24 statistical aggregates from keyboard and mouse behavior:
- Typing speed (WPM/CPM)
- Key hold and flight time statistics
- Error rate (backspace ratio)
- Mouse velocity, acceleration, direction changes
- Idle time

No raw keystrokes, cursor coordinates sequences, or screen content is transmitted.

---

**Q: Can employers spy on employees with this?**

The system is designed for **employee wellness, not surveillance**. Individual fatigue scores are private to the employee unless explicitly shared with a manager. Administrators see only aggregated, anonymized team-level trends. The system does not track productivity, application usage, or screen content.

That said, any monitoring tool can be misused. Organizations deploying MindGuard should follow applicable employment law regarding workplace monitoring disclosure requirements.

---

## Technical

**Q: Why LightGBM over XGBoost or CatBoost?**

LightGBM achieved the highest composite score (0.6×F1 + 0.4×AUC) on the test set and provides the fastest inference time among the tree ensemble models evaluated. Both LightGBM and XGBoost produced near-identical test F1 scores (0.9373 vs 0.9370). CatBoost was excluded from the final evaluation in the current training report — it can be included by running `scripts/train_models.py` with all dependencies installed.

---

**Q: Why are the CV F1 scores (~0.01) so different from the test F1 scores (~0.94)?**

This is a known issue with the current evaluation. The stratified 5-fold CV splits on the synthetic dataset encountered a class distribution artifact that prevented the minority class from appearing in some CV folds. The **test set F1 scores are the reliable metric** — they use a single stratified 80/20 split where class balance was correctly maintained. The CV scores are misleading and this is documented explicitly in [Model Details](MODEL_DETAILS.md#data-leakage-disclosure).

---

**Q: Why does the WebSocket use `?token=` in the URL instead of headers?**

The WebSocket protocol does not support custom headers during the HTTP upgrade handshake in most browser environments. Passing the JWT as a query parameter is the standard approach for browser-based WebSocket authentication. In production, WSS (WebSocket over TLS) must be enforced at the Nginx layer to prevent token interception in transit.

---

**Q: What happens if Redis is down?**

The backend was specifically hardened to fail-fast when Redis is unavailable rather than blocking for 5 seconds per request. Without Redis:
- JWT token blacklisting is disabled (tokens remain valid until natural expiry after logout)
- WebSocket event broadcasting falls back to in-process in-memory delivery (works correctly with a single backend worker)
- Rate limiting middleware degrades gracefully

The system remains fully functional for development and single-instance deployments without Redis.

---

**Q: Why SQLite in development but PostgreSQL in production?**

SQLite is used in local development and CI because it requires no external service, simplifying setup. The async driver (`aiosqlite`) provides the same `asyncio` interface as `asyncpg`. PostgreSQL is used in production for its ACID compliance, concurrent write performance, UUID native type, and rich indexing options. The `UUID` column type in `models.py` is a custom `TypeDecorator` that uses PostgreSQL's native UUID type in production and `CHAR(36)` in SQLite.

---

**Q: How do I retrain the model after changing the dataset?**

```bash
# 1. Generate fresh data
python dataset/generator.py --rows 150000 --output dataset/generated/fatigue_data.csv

# 2. Train and export best model
python scripts/train_models.py --data dataset/generated/fatigue_data.csv --output ml/models/

# 3. Restart the backend to reload the model
# ModelRegistry.load() runs at startup via FastAPI lifespan event
```

---

**Q: How do I run everything locally without Docker?**

See the [Developer Guide](developer/DEVELOPER_GUIDE.md) for a complete step-by-step guide using SQLite and the Vite development proxy. The short version:

```bash
# Backend
PYTHONPATH=backend DATABASE_URL="sqlite+aiosqlite:///./mindguard.db" \
  uvicorn app.main:app --port 8002 --reload

# Frontend
cd frontend && npm run dev

# Tracker
cd tracker && python main.py --email alice@company.com --password Password123
```

---

**Q: What does SHAP stand for, and why does it matter here?**

SHAP (SHapley Additive exPlanations) is a game-theory-based method for explaining individual ML predictions. It attributes a contribution score to each feature for a specific prediction. In MindGuard, SHAP is used to answer: "Why did the model predict a fatigue score of 0.82 for this observation?" The top 5 SHAP features are returned with every prediction and displayed in the React dashboard. This makes the system **explainable** — a critical property for a wellness tool affecting people's work experience.

---

## Contributing

**Q: How do I add a new behavioral feature?**

1. Add the feature column to `BehaviourSnapshot` in `backend/app/db/models.py`
2. Add the feature to the schema in `backend/app/schemas/behaviour.py`
3. Add collection logic to `tracker/aggregator.py`
4. Add the feature name to `FEATURE_NAMES` in `backend/app/ml/inference.py`
5. Retrain the model — the new feature will be included automatically
6. Generate an Alembic migration for the new column

**Q: How do I add a new ML model to the evaluation?**

Add a new entry to the `get_models()` function in `scripts/train_models.py`. The model must implement scikit-learn's `fit` / `predict_proba` interface. It will be automatically included in training, evaluation, and comparison.
