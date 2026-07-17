# 🧠 MindGuard — Real-Time Mental Fatigue Detection

> **Production-quality AI application for monitoring mental fatigue through keyboard and mouse behavioral patterns.**

[![License: MIT](https://img.shields.io/badge/License-MIT-cyan.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6.svg)](https://typescriptlang.org)

---

## 🌟 Overview

MindGuard is a **privacy-preserving**, **non-invasive** mental fatigue detection system designed for enterprise employee wellness monitoring. It uses only keyboard and mouse behavioral patterns — **no webcam, no microphone, no wearables**.

### Key Features

- 🔴 **Real-time fatigue scoring** with sub-10ms ML inference
- 🔒 **Privacy by design** — no keystrokes stored, only timing metrics
- 🤖 **AI-powered with SHAP explainability** — know *why* a score is given
- 📊 **Comprehensive analytics** — hourly/daily/weekly trends + heatmaps
- 💡 **Smart recommendations** — context-aware break suggestions
- 🔔 **Multi-channel notifications** — in-app, WebSocket push, email
- 👥 **Admin dashboard** — team-wide monitoring and high-risk alerts
- ⚡ **WebSocket live updates** — real-time score streaming to dashboard
- 🐳 **Docker-ready** — full stack deployment in one command

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MindGuard Architecture                    │
├──────────────┬──────────────────────┬───────────────────────┤
│ Desktop      │   FastAPI Backend    │  React Frontend       │
│ Tracker      │                      │                       │
│              │  ┌───────────────┐   │  ┌─────────────────┐ │
│ keyboard.py  │  │  REST API v1  │   │  │   Dashboard     │ │
│ mouse.py     │──│  /api/v1/*    │   │  │   Analytics     │ │
│ aggregator   │  └───────┬───────┘   │  │   Admin Panel   │ │
│ sender.py    │          │            │  └────────┬────────┘ │
│              │  ┌───────┴───────┐   │           │          │
└──────────────┘  │  ML Engine    │   │  ┌────────┴────────┐ │
                  │  RF/XGB/LGBM  │   │  │ WebSocket Hook  │ │
                  │  SHAP Values  │   │  │ Zustand Store   │ │
                  └───────┬───────┘   │  └─────────────────┘ │
                          │            └───────────────────────┘
                  ┌───────┴───────┐
                  │  PostgreSQL   │
                  │  Redis Cache  │
                  │  Redis Pub/Sub│
                  └───────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI 0.110+, SQLAlchemy 2.0 (async), Python 3.11+ |
| **ML** | scikit-learn, XGBoost, LightGBM, CatBoost, SHAP |
| **Database** | PostgreSQL 16 (async via asyncpg) |
| **Cache/Queue** | Redis 7 (JWT blacklist + WebSocket Pub/Sub) |
| **Frontend** | React 18 + TypeScript + Vite 5 |
| **Styling** | Tailwind CSS v4 + Framer Motion |
| **State** | Zustand + React Query |
| **Charts** | Recharts |
| **Tracker** | pynput (keyboard + mouse) |
| **DevOps** | Docker Compose + Nginx |

---

## 📁 Project Structure

```
mental_fatigue_detector/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST API endpoints
│   │   │   ├── auth.py          # JWT auth, signup, login, logout
│   │   │   ├── behaviour.py     # Snapshot ingestion
│   │   │   ├── sessions.py      # Session management
│   │   │   ├── predictions.py   # Prediction history
│   │   │   ├── analytics.py     # Dashboard analytics
│   │   │   ├── recommendations.py
│   │   │   ├── notifications.py
│   │   │   ├── users.py
│   │   │   └── admin.py
│   │   ├── core/                # Security, config, exceptions
│   │   ├── db/                  # SQLAlchemy models + session
│   │   ├── ml/                  # ML inference + model registry
│   │   ├── services/            # Prediction orchestration
│   │   ├── websocket/           # WebSocket manager + Pub/Sub
│   │   └── main.py              # FastAPI entry point
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── api/                 # Axios client + typed API modules
│       ├── components/          # Reusable UI components
│       │   ├── auth/            # Protected route
│       │   ├── layout/          # Dashboard layout + sidebar
│       │   ├── dashboard/       # Gauge, charts, explainability
│       │   └── analytics/       # Heatmap
│       ├── hooks/               # useWebSocket
│       ├── pages/               # Route-level page components
│       ├── store/               # Zustand stores (auth, fatigue)
│       └── types/               # TypeScript domain types
│
├── dataset/
│   └── generator.py             # 150k+ synthetic data generator
│
├── scripts/
│   └── train_models.py          # Full ML training pipeline
│
├── tracker/
│   ├── keyboard_collector.py    # Privacy-preserving KB tracker
│   ├── mouse_collector.py       # Mouse event collector
│   ├── aggregator.py            # 1-second feature windows
│   └── main.py                  # Tracker CLI orchestrator
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
│
├── docker-compose.yml           # Production stack
└── docker-compose.dev.yml       # Development stack
```

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop 4.x+
- Python 3.11+ (for tracker and ML scripts)
- Node.js 20+ (for frontend development)

### 1. Clone & Configure

```bash
git clone https://github.com/yourorg/mindguard.git
cd mindguard
cp .env.example .env
# Edit .env with your settings (JWT secret, etc.)
```

### 2. Start Infrastructure

```bash
# Development (with hot reload)
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose up -d
```

The app will be available at:
- **Frontend:** http://localhost:80
- **API:** http://localhost:8000/api/v1
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 3. Generate Dataset & Train Models

```bash
# Install ML dependencies
pip install -r scripts/requirements.txt

# Generate 150,000 row synthetic dataset
python dataset/generator.py --rows 150000 --output dataset/generated/fatigue_data.csv

# Train all models, compare, select best, export
python scripts/train_models.py --data dataset/generated/fatigue_data.csv --output ml/models/

# Output: ml/models/best_model.joblib + scaler.joblib + training_report.json
```

### 4. Start Desktop Tracker

```bash
# Install tracker dependencies
pip install -r tracker/requirements.txt

# Start tracking (with email/password login)
python tracker/main.py \
  --api-url http://localhost:8000 \
  --email you@company.com \
  --password YourPassword

# Or with existing JWT token
python tracker/main.py \
  --api-url http://localhost:8000 \
  --token <jwt_token>
```

---

## 🤖 ML Pipeline

### Feature Engineering (24+ features)

**Keyboard Metrics:**
| Feature | Description |
|---------|-------------|
| `typing_speed_wpm` | Words per minute |
| `key_hold_time_ms` | Average key press duration |
| `flight_time_ms` | Inter-keystroke delay |
| `error_rate` | Backspace/total keystroke ratio |
| `typing_rhythm_variance` | Variance in inter-keystroke intervals |
| `typing_burst_score` | Ratio of active typing spans |
| `idle_time_keyboard_s` | Keyboard inactivity periods |

**Mouse Metrics:**
| Feature | Description |
|---------|-------------|
| `mouse_speed_px_s` | Average cursor velocity |
| `mouse_acceleration` | Speed change over time |
| `direction_changes` | Jitter / tremor indicator |
| `click_frequency` | Clicks per minute |
| `hover_duration_ms` | Time spent hovering (hesitation) |
| `double_click_count` | Misclick proxy |
| `idle_time_mouse_s` | Mouse inactivity periods |

### Models Compared

| Model | CV F1 | Test F1 | Test AUC |
|-------|-------|---------|----------|
| XGBoost | ~0.91 | ~0.92 | ~0.97 |
| LightGBM | ~0.91 | ~0.91 | ~0.96 |
| Random Forest | ~0.89 | ~0.90 | ~0.95 |
| CatBoost | ~0.90 | ~0.91 | ~0.96 |
| Logistic Regression | ~0.82 | ~0.82 | ~0.88 |
| SVM | ~0.84 | ~0.84 | ~0.91 |

*Actual scores depend on dataset and hyperparameters.*

### SHAP Explainability

Every prediction includes:
- Top 5 contributing features with SHAP values
- Direction (increases/decreases fatigue)
- Feature value at prediction time
- Human-readable explanation text

---

## 🔒 Privacy Architecture

MindGuard is designed privacy-first:

1. **No keystroke content** — only timing between events is recorded
2. **Local aggregation** — raw events never leave the device; only the 24-feature summary is transmitted
3. **Encrypted in transit** — HTTPS/WSS only
4. **Encrypted at rest** — passwords bcrypt-hashed, tokens JWT-signed
5. **Token blacklisting** — logout immediately revokes tokens via Redis
6. **Minimal data retention** — configurable retention policies
7. **Employee control** — users can pause/stop tracking at any time

---

## 📡 API Overview

### Authentication
```
POST /api/v1/auth/signup         Register new user
POST /api/v1/auth/login          Login (returns JWT)
POST /api/v1/auth/refresh        Refresh access token
POST /api/v1/auth/logout         Revoke token
GET  /api/v1/auth/me             Current user profile
```

### Behaviour Ingestion
```
POST /api/v1/behaviour/snapshot  Send 1-second feature window
POST /api/v1/behaviour/batch     Send batch of windows
```

### Analytics
```
GET  /api/v1/analytics/summary   Dashboard summary stats
GET  /api/v1/analytics/daily     Hourly trend for today
GET  /api/v1/analytics/weekly    Daily trend for 7 days
GET  /api/v1/analytics/heatmap   Hour×Weekday heatmap
```

### Real-Time
```
WS   /ws/{user_id}?token=<jwt>   Live fatigue score stream
```

Full API documentation available at `/docs` when running.

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=html

# Frontend type check
cd frontend
npx tsc --noEmit

# Frontend unit tests
npm run test
```

---

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | FastAPI app (4 workers) |
| `frontend` | 80 | Nginx + React build |
| `postgres` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ for employee wellness. Privacy always comes first.*
