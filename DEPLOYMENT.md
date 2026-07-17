# MindGuard Deployment Guide

This guide outlines how to deploy the MindGuard platform in a production environment.

## 1. Prerequisites

- **Docker & Docker Compose**: The easiest way to run the backend services.
- **Node.js (v18+)**: To build the frontend bundle.
- **Python (3.12+)**: If running the backend natively instead of Docker.

---

## 2. Infrastructure (Docker)

MindGuard's backend relies on PostgreSQL (for persistence) and Redis (for rate limiting and WebSocket pub/sub).

1. Clone the repository to your production server.
2. Review the `docker-compose.yml` (if available) or use the development `docker-compose.dev.yml` as a template for production.
3. Boot the infrastructure:
   ```bash
   docker-compose up -d db redis
   ```

---

## 3. Backend Deployment

The FastAPI backend should be run behind a reverse proxy like Nginx or Traefik, managed by a process manager (e.g., Gunicorn + Uvicorn) or inside a Docker container.

### Option A: Using Docker (Recommended)
1. Build the backend image:
   ```bash
   docker build -t mindguard-backend ./backend
   ```
2. Run the container, ensuring it is attached to the same network as the DB and Redis containers, and injecting the `.env` file:
   ```bash
   docker run -d -p 8000:8000 --env-file .env mindguard-backend
   ```

### Option B: Native Deployment (Gunicorn)
1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Run using Gunicorn with Uvicorn workers:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

---

## 4. Frontend Deployment

The React frontend is a static bundle that can be hosted on any static file server, CDN (e.g., Vercel, Netlify, Cloudflare Pages), or Nginx.

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set the production API URL in `.env.production`:
   ```
   VITE_API_URL=https://api.yourdomain.com/api/v1
   ```
4. Build the production bundle:
   ```bash
   npm run build
   ```
5. Serve the `dist/` folder using Nginx:
   ```nginx
   server {
       listen 80;
       server_name app.yourdomain.com;
       root /path/to/frontend/dist;
       index index.html;

       location / {
           try_files $uri $uri/ /index.html;
       }
   }
   ```

---

## 5. Desktop Tracker Deployment

The Python tracker must run on the end-user's machine. For a company-wide deployment, it should be bundled into a standalone executable.

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build the executable:
   ```bash
   cd tracker
   pyinstaller --onefile --noconsole main.py
   ```
3. Distribute the generated `dist/main.exe` (Windows) or binary to employees.

**Configuration:** The tracker requires an authentication token and the backend URL. These can be passed via a local `.env` file distributed alongside the executable, or baked into the binary during a custom build process for your organization.
