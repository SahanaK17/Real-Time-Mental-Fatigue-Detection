# Roadmap

This document tracks the evolution of MindGuard from its current v1.0 state toward a production-validated enterprise wellness platform.

---

**Navigation:** [← Back to README](../README.md)

---

## Current State — v1.0.0 (Released)

### Infrastructure & Architecture
- [x] Async FastAPI backend with Uvicorn
- [x] PostgreSQL persistence with SQLAlchemy 2.0 async
- [x] Redis Pub/Sub for horizontal WebSocket scaling
- [x] JWT authentication with refresh token rotation and Redis blacklisting
- [x] Docker Compose full-stack deployment
- [x] Nginx reverse proxy configuration
- [x] Graceful Redis fail-fast (operates without Redis in development)

### Machine Learning
- [x] LightGBM classifier selected from 5-model evaluation
- [x] SHAP TreeExplainer for per-prediction explainability
- [x] Heuristic fallback when model is not loaded
- [x] Synthetic dataset generator (150k+ rows)
- [x] Training pipeline with cross-validation and model selection

### Data Collection
- [x] Privacy-preserving desktop tracker (pynput)
- [x] Keyboard dynamics (flight time, hold time, error rate, rhythm variance)
- [x] Mouse kinematics (velocity, acceleration, jitter, idle time)
- [x] 1-second aggregation window
- [x] Native OS notification via plyer on high-fatigue alert

### Frontend
- [x] Real-time fatigue gauge (WebSocket)
- [x] Hourly and weekly trend charts (Recharts)
- [x] Day × hour fatigue heatmap
- [x] Admin user management panel
- [x] CSV and PDF report export
- [x] SHAP feature importance view

### Documentation
- [x] Architecture diagrams (Mermaid)
- [x] API reference with full request/response schemas
- [x] Developer setup guide
- [x] Deployment guide (Docker, native, Nginx)
- [x] ML model details with honest evaluation disclosure
- [x] Dataset transparency document
- [x] Security policy and vulnerability disclosure process
- [x] Contributing guide and Code of Conduct

---

## Near-Term — v1.1.0 (Target: Q4 2026)

### Testing & Quality
- [ ] Integration test suite covering all API endpoints
- [ ] Frontend E2E tests (Playwright)
- [ ] CI coverage gate (minimum 70%)
- [ ] Pre-commit hooks (Ruff + Prettier)

### ML Improvements
- [ ] Address CV F1 anomaly — fix class imbalance in stratified splitting
- [ ] Per-user baseline calibration (adapt to individual typing patterns)
- [ ] 15-minute rolling window prediction (temporal context)
- [ ] Confidence interval output alongside point predictions

### Infrastructure
- [ ] Alembic migrations replacing `create_all` in development
- [ ] Structured log aggregation (compatible with Loki/ELK)
- [ ] Docker Compose health-dependent startup ordering
- [ ] Kubernetes Helm chart (basic)

---

## Medium-Term — v2.0.0 (Target: 2027)

### Real-World Validation
- [ ] IRB-compliant participant study for real behavioral data collection
- [ ] Ground-truth label collection (KSS self-reports + NASA-TLX)
- [ ] Model retraining and re-evaluation on real-world dataset
- [ ] Publication of methodology and anonymized benchmark

### Personalization
- [ ] Per-user baseline calibration period (first 7 days)
- [ ] User-specific fatigue threshold adjustment
- [ ] Circadian rhythm modeling (time-of-day normalization)
- [ ] Historical trend analysis for long-term pattern detection

### Enterprise Features
- [ ] SAML 2.0 / OAuth2 Enterprise SSO
- [ ] Organization and team grouping
- [ ] Manager-level team fatigue dashboard (aggregate, anonymized)
- [ ] Role-based data access policies
- [ ] Scheduled wellness reports (email/Slack)

### Deployment
- [ ] Native desktop installer for tracker (Tauri or Electron)
- [ ] Auto-update mechanism for tracker
- [ ] Multi-region deployment support

---

## Long-Term Vision — v3.0+ (2028+)

- [ ] Multimodal signals (optional: webcam posture analysis, wearable integration)
- [ ] Federated learning — model improves from real data without centralizing it
- [ ] Mobile companion app (iOS / Android) for break reminders
- [ ] Integration with calendar systems (Google, Outlook) for context-aware alerts
- [ ] Public research dataset release (anonymized, with participant consent)

---

## Declined / Out of Scope

| Feature | Reason |
|:---|:---|
| Keystroke logging (content) | Core privacy principle — will never be implemented |
| Screen capture / recording | Core privacy principle — will never be implemented |
| Real-time HR metric for managers | Individual scores are private by design |
| Gamification of fatigue reduction | Risk of perverse incentives; deferred |
