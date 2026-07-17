# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-07-17

### Added
- **Authentication pipeline:** JWT-based login, signup, logout with Redis token blacklisting and refresh token rotation.
- **Behavioral data ingestion:** `/behaviour/snapshot` and `/behaviour/batch` endpoints for real-time feature vector submission from the Desktop Tracker.
- **ML inference engine:** LightGBM model loaded in-memory at startup, performing sub-10ms inference with SHAP explainability per prediction.
- **WebSocket streaming:** Per-user authenticated WebSocket channels with Redis Pub/Sub for horizontal scalability.
- **React dashboard:** Real-time fatigue gauge, hourly/weekly trend charts, and fatigue heatmap.
- **Analytics endpoints:** Summary, daily, weekly, and heatmap aggregation queries.
- **Admin panel:** User management, high-risk user identification, and CSV/PDF report export.
- **Desktop Tracker:** Python agent with keystroke dynamics and mouse kinematic collection. Aggregates features locally in 1-second windows. Triggers native OS notifications on high-fatigue alerts.
- **Synthetic dataset generator:** Generates 150,000+ synthetic behavioral records for ML training.
- **Multi-model training pipeline:** Evaluates and compares Random Forest, XGBoost, LightGBM, SVM, and Logistic Regression.
- **Docker Compose deployment:** Full-stack orchestration with PostgreSQL, Redis, backend, and frontend.
- **Redis fail-fast:** Backend gracefully disables caching if Redis is unreachable, preventing request timeouts.
- **Windows-compatible logging:** Structured logging using `structlog` with ASCII-safe output for Windows console compatibility.

### Security
- bcrypt password hashing (work factor 12)
- JWT token blacklisting via Redis JTI index
- CORS origin allowlist
- Per-IP rate limiting (SlowAPI middleware)
- Pydantic schema validation on all API endpoints
