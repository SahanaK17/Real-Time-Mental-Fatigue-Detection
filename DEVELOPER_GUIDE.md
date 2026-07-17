# MindGuard Developer Guide

Welcome to the MindGuard developer guide! This document will help you set up your local development environment and understand the contribution workflow.

## 1. Project Structure

The repository is organized into four main directories:
- `backend/`: FastAPI application, database schemas, and ML inference logic.
- `frontend/`: React dashboard application built with Vite and Tailwind CSS.
- `tracker/`: Python desktop agent for collecting interaction metrics.
- `dataset/`: Synthetic dataset generation and ML model training scripts.

---

## 2. Setting Up the Backend

We use `uv` for lightning-fast Python dependency management.

1. Ensure Python 3.12+ and `uv` are installed.
2. Create and activate a virtual environment in the project root:
   ```bash
   uv venv
   source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
   ```
3. Install the dependencies:
   ```bash
   uv pip install -r backend/requirements.txt
   uv pip install aiosqlite  # If running SQLite locally instead of Postgres
   ```
4. Configure the environment by copying the example `.env` file:
   ```bash
   cp backend/.env.example backend/.env
   ```
5. Start the development server (Windows PowerShell):
   ```powershell
   $env:PYTHONPATH="backend"
   $env:DATABASE_URL="sqlite+aiosqlite:///./mindguard.db"
   .venv\Scripts\python.exe -m uvicorn app.main:app --port 8002 --reload
   ```

---

## 3. Setting Up the Frontend

The frontend uses Node.js and `npm`.

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
The dashboard will be available at `http://localhost:5173`.

---

## 4. Working with the Machine Learning Models

The ML pipeline is located in the `dataset/` directory.

1. Generate synthetic data (if needed):
   ```bash
   python dataset/generator.py
   ```
2. Train the models:
   ```bash
   python scripts/train_models.py
   ```
This script will evaluate Random Forest, Gradient Boosting, SVM, Neural Network, and LightGBM. It will automatically save the best-performing model to `backend/app/ml/models/best_model.joblib`.

---

## 5. Development Workflows & Best Practices

- **Linting & Formatting**: We recommend using `ruff` for Python formatting and `prettier` for frontend code.
- **Commit Messages**: Write clear, descriptive commit messages.
- **Database Migrations**: Alembic is configured for database migrations. If you change a model in `backend/app/models`, generate a new migration:
  ```bash
  alembic revision --autogenerate -m "Description of change"
  alembic upgrade head
  ```
- **Testing**: Ensure any new backend logic includes comprehensive `pytest` tests. Run them using:
  ```bash
  pytest backend/tests/
  ```

Happy Coding!
