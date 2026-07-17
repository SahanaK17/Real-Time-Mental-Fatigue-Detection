# Developer Guide

This guide covers setting up a local development environment for all three MindGuard components: the FastAPI backend, the React frontend, and the Python Desktop Tracker.

---

**Navigation:** [← Back to README](../../README.md) | [API Reference](../api/API.md) | [Architecture](../architecture/ARCHITECTURE.md) | [Deployment](../deployment/DEPLOYMENT.md)

---

## Table of Contents

- [Repository Structure](#repository-structure)
- [Backend Setup](#1-backend-setup)
- [Frontend Setup](#2-frontend-setup)
- [Desktop Tracker Setup](#3-desktop-tracker-setup)
- [ML Pipeline](#4-ml-pipeline)
- [Coding Standards](#5-coding-standards)
- [Testing](#6-testing)
- [Database Migrations](#7-database-migrations)

---

## Repository Structure

```text
mindguard/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # Route handlers
│   │   ├── core/                # Auth, config, Redis, exceptions
│   │   ├── db/                  # SQLAlchemy models and session
│   │   ├── ml/                  # Inference engine and model registry
│   │   └── websocket/           # Pub/Sub connection manager
│   └── requirements.txt
├── docs/                        # All documentation (you are here)
├── frontend/
│   └── src/
│       ├── api/                 # Axios clients and interceptors
│       ├── components/          # Reusable UI components
│       ├── hooks/               # Custom hooks (useWebSocket, etc.)
│       ├── pages/               # Page-level view components
│       └── store/               # Zustand global state
├── tracker/
│   ├── keyboard_collector.py   # Keystroke dynamics collection
│   ├── mouse_collector.py      # Mouse kinematics collection
│   ├── aggregator.py           # Statistical feature engineering
│   └── main.py                 # CLI entry point
├── dataset/                    # Synthetic data generation tools
├── scripts/                    # ML training and evaluation pipeline
└── ml/
    ├── models/                 # Serialized models (not committed to VCS)
    └── pipeline/
```

---

## 1. Backend Setup

The backend uses Python 3.11+ and `uv` for fast dependency management. For local development, SQLite is used instead of PostgreSQL.

### Step 1: Create the virtual environment
```bash
# From the repository root
python -m venv .venv
# Activate (Linux/macOS)
source .venv/bin/activate
# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### Step 2: Install dependencies
```bash
uv pip install -r backend/requirements.txt
uv pip install aiosqlite   # SQLite async driver for local development
```

### Step 3: Configure environment
```bash
cp .env.example .env
# Edit .env — the defaults will work for local SQLite development
```

### Step 4: Start the development server
```powershell
# Windows PowerShell
$env:PYTHONPATH = "backend"
$env:DATABASE_URL = "sqlite+aiosqlite:///./mindguard.db"
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8002 --reload
```

```bash
# Linux/macOS
PYTHONPATH=backend DATABASE_URL="sqlite+aiosqlite:///./mindguard.db" \
  uvicorn app.main:app --port 8002 --reload
```

The API is now available at `http://localhost:8002`. Interactive API docs at `http://localhost:8002/docs`.

---

## 2. Frontend Setup

The frontend uses Node.js 20 LTS and communicates with the backend through Vite's development proxy.

### Step 1: Install dependencies
```bash
cd frontend
npm install
```

### Step 2: Start the development server
```bash
npm run dev
```

The dashboard is now available at `http://localhost:5173`. API requests are proxied to `http://localhost:8002` via the Vite config, eliminating CORS issues during development.

---

## 3. Desktop Tracker Setup

The tracker runs on the host machine (not in Docker) and requires OS-level input access.

```bash
cd tracker
pip install -r requirements.txt
```

Run the tracker against the local backend:
```bash
python main.py \
  --email alice@company.com \
  --password Password123 \
  --api-url http://localhost:8002 \
  --interval 1.0
```

The tracker will authenticate, start a session, and begin sending behavioral feature snapshots every second.

---

## 4. ML Pipeline

To retrain the model from scratch:

### Step 1: Generate synthetic training data
```bash
python dataset/generator.py --rows 150000 --output dataset/generated/fatigue_data.csv
```

### Step 2: Train and evaluate all models
```bash
python scripts/train_models.py \
  --data dataset/generated/fatigue_data.csv \
  --output ml/models/
```

This evaluates Random Forest, XGBoost, LightGBM, SVM, and Logistic Regression. The model with the highest test F1 score is serialized to `ml/models/best_model.joblib`. A training report is written to `ml/models/training_report.json`.

---

## 5. Coding Standards

| Language | Formatter | Linter |
|:---|:---|:---|
| Python | `ruff format` | `ruff check` |
| TypeScript / TSX | `prettier` | `eslint` |

Run before committing:
```bash
# Python
ruff format backend/ tracker/ dataset/ scripts/
ruff check backend/ tracker/ dataset/ scripts/

# TypeScript
cd frontend && npm run lint && npm run format
```

**Commit message convention:** Use [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: add WebSocket reconnection with exponential backoff
fix: resolve race condition in session end handler
docs: update API reference for /behaviour/batch endpoint
refactor: extract ML inference into background task
```

---

## 6. Testing

```bash
# Backend — pytest with coverage
cd backend
pytest --cov=app --cov-report=term-missing

# Frontend — TypeScript type checking (no type errors)
cd frontend
npx tsc --noEmit

# Frontend — component tests
cd frontend
npm run test
```

---

## 7. Database Migrations

Alembic is configured for schema migrations. When you modify a SQLAlchemy model in `backend/app/db/models.py`:

```bash
# Generate a new migration
cd backend
alembic revision --autogenerate -m "description of your change"

# Review the generated migration file, then apply it
alembic upgrade head

# To roll back one step
alembic downgrade -1
```
