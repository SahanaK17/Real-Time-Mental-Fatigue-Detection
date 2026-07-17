# MindGuard Architecture

MindGuard is a distributed, real-time mental fatigue detection system designed for enterprise deployments. It leverages machine learning to analyze user interaction patterns (keystrokes, mouse movements) to infer mental fatigue without invading user privacy (no keylogging, no screen recording).

## System Components

### 1. Desktop Tracker (`/tracker`)
A lightweight, background Python application running on the user's machine.
- **Role**: Collects interaction timings and distances.
- **Mechanism**: Hooks into OS-level input events using `pynput`. Aggregates events into 10-minute sliding windows.
- **Privacy**: Only captures *timings* (time between keys, duration of press) and *distances* (pixels moved). It explicitly discards the actual keys pressed to preserve strict privacy.
- **Feedback**: Maintains a WebSocket connection to the backend to receive real-time fatigue alerts. If fatigue is high, it triggers native desktop OS popups (using `plyer`) suggesting wellness breaks.

### 2. FastAPI Backend (`/backend`)
A high-performance, asynchronous REST API serving as the central nervous system.
- **Role**: Handles authentication, data persistence, and ML model inference.
- **Tech Stack**: FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis.
- **Machine Learning**: 
  - Loads a pre-trained **LightGBM** model (`best_model.joblib`) into memory on startup.
  - Exposes an inference endpoint (`/predictions/metrics`) that the tracker hits.
  - Real-time scoring allows it to dispatch WebSocket events immediately upon detecting fatigue.
- **Admin Utilities**: Generates streaming CSVs and dynamic PDF reports (via `reportlab`) directly from memory for administrators.

### 3. React Frontend (`/frontend`)
A dynamic, responsive, and highly polished web dashboard.
- **Role**: Allows users to view their historical fatigue metrics and administrators to manage the platform.
- **Tech Stack**: React 18 (Vite), TypeScript, Tailwind CSS, Framer Motion, Recharts.
- **Design Philosophy**: Emphasizes a modern, "glassmorphism" aesthetic with smooth micro-animations to create a premium enterprise feel.
- **Features**: Real-time fatigue gauges, historical heatmaps, admin user management, and report generation triggers.

---

## Data Flow

1. **Collection**: The Tracker collects metrics over a rolling window.
2. **Transmission**: The Tracker POSTs the aggregated metrics to the Backend (`/predictions/metrics`).
3. **Inference**: The Backend passes the metrics through the loaded LightGBM model.
4. **Persistence**: The Backend saves the prediction result (e.g., fatigue score 0.85) to the PostgreSQL database.
5. **Alerting**: If the score exceeds the critical threshold (e.g., 0.75), the Backend sends a WebSocket message to the specific user's active Tracker.
6. **Notification**: The Tracker receives the WebSocket message and triggers a local OS popup.
7. **Visualization**: The Frontend fetches historical data from the Backend to populate charts and dashboards.

---

## Machine Learning Pipeline
The ML pipeline (`/scripts/train_models.py` and `/dataset`) was used to generate synthetic behavioral data and train multiple models. **LightGBM** was selected as the production model due to its superior F1 score (0.9373) and ultra-low latency inference times, making it ideal for real-time processing within the FastAPI request lifecycle.
