# Deployment Guide

This guide covers deploying MindGuard in a production environment, from infrastructure setup through to distributing the Desktop Tracker to end users.

---

**Navigation:** [← Back to README](../../README.md) | [API Reference](../api/API.md) | [Architecture](../architecture/ARCHITECTURE.md) | [Developer Guide](../developer/DEVELOPER_GUIDE.md)

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Deployment (Recommended)](#docker-deployment-recommended)
- [Backend — Native Deployment](#backend--native-deployment)
- [Frontend — Production Build](#frontend--production-build)
- [Nginx Configuration](#nginx-configuration)
- [Desktop Tracker Distribution](#desktop-tracker-distribution)
- [Environment Variable Checklist](#environment-variable-checklist)

---

## Prerequisites

| Dependency | Version | Purpose |
|:---|:---:|:---|
| Docker | 24.x+ | Container orchestration |
| Docker Compose | 2.x+ | Multi-service management |
| Python | 3.11+ | Backend / Tracker runtime |
| Node.js | 20 LTS+ | Frontend build |

---

## Docker Deployment (Recommended)

The recommended deployment path uses Docker Compose to orchestrate all services (PostgreSQL, Redis, Backend, Frontend with Nginx).

**1. Configure environment variables:**
```bash
cp .env.example .env
# Edit .env — ensure all placeholder values are replaced before proceeding
```

> **Warning:** Do not deploy with default `SECRET_KEY` or `JWT_SECRET_KEY` values. Generate strong random keys:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

**2. Start all services:**
```bash
docker-compose up --build -d
```

**3. Verify all services are healthy:**
```bash
docker-compose ps
curl http://localhost:8002/health
```

Services will be available at:

| Service | URL |
|:---|:---|
| Web Dashboard | `http://localhost:80` |
| API | `http://localhost:8002/api/v1` |
| API Docs (Swagger) | `http://localhost:8002/docs` |

---

## Backend — Native Deployment

For environments without Docker, the backend can be run natively behind Gunicorn.

**1. Install dependencies:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Apply database migrations:**
```bash
alembic upgrade head
```

**3. Start with Gunicorn:**
```bash
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8002 \
  --log-level info
```

---

## Frontend — Production Build

The React frontend compiles to a static bundle suitable for any CDN, static host, or Nginx.

**1. Install dependencies:**
```bash
cd frontend
npm install
```

**2. Set the production API URL:**
```bash
# frontend/.env.production
VITE_API_BASE_URL=https://api.yourdomain.com
```

**3. Build the production bundle:**
```bash
npm run build
# Output: frontend/dist/
```

**4. Deploy:** The `dist/` directory can be served by Nginx, Vercel, Netlify, Cloudflare Pages, or any static host.

---

## Nginx Configuration

A reference Nginx configuration for serving both the API (reverse proxy) and frontend (static files) from a single server.

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend — static bundle
    root /var/www/mindguard/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend — reverse proxy
    location /api/ {
        proxy_pass         http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass         http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

---

## Desktop Tracker Distribution

For company-wide deployment, the Python tracker should be packaged as a standalone native executable so employees do not need to manage a Python installation.

**1. Install PyInstaller:**
```bash
pip install pyinstaller
```

**2. Build the executable:**
```bash
cd tracker
pyinstaller --onefile --noconsole main.py
```

**3. Distribute:** The compiled binary is output to `tracker/dist/main.exe` (Windows). Distribute it alongside a pre-configured `.env` file or bake the `--api-url` and `--email` arguments into a launch script for automated onboarding.

---

## Environment Variable Checklist

Before going live, verify every required environment variable is set correctly.

| Variable | Status | Notes |
|:---|:---:|:---|
| `SECRET_KEY` | Required | Must be ≥ 32 random characters |
| `JWT_SECRET_KEY` | Required | Must be ≥ 32 random characters |
| `DATABASE_URL` | Required | Full PostgreSQL async connection string |
| `REDIS_URL` | Required | Full Redis connection string |
| `CORS_ORIGINS` | Required | Set to your frontend domain(s) only |
| `APP_ENV` | Required | Set to `production` |
| `DEBUG` | Required | Must be `false` in production |
| `LOG_LEVEL` | Recommended | Set to `WARNING` or `ERROR` in production |
| `SMTP_*` | Optional | Required only if email alerts are enabled |
