# MindGuard API Documentation

This document outlines the RESTful API and WebSocket interfaces provided by the MindGuard backend.

## Base URL
All REST endpoints are relative to:
```
http://<host>:<port>/api/v1
```

## Authentication
Most endpoints require authentication via JSON Web Tokens (JWT).
Include the token in the `Authorization` header as a Bearer token:
```
Authorization: Bearer <your_access_token>
```

---

## 1. Authentication Endpoints

### `POST /auth/signup`
Creates a new user account.
* **Body:**
  ```json
  {
    "email": "user@company.com",
    "password": "securepassword123",
    "full_name": "John Doe",
    "department": "Engineering",
    "job_title": "Software Engineer"
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "id": "uuid",
    "email": "user@company.com",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true
  }
  ```

### `POST /auth/login`
Authenticates a user and returns an access token.
* **Body:**
  ```json
  {
    "email": "user@company.com",
    "password": "securepassword123"
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhb...",
    "token_type": "bearer",
    "user": { ... }
  }
  ```

---

## 2. Session Management

### `POST /sessions/start`
Starts a new tracking session.
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "id": "uuid",
    "user_id": "uuid",
    "start_time": "2026-07-14T10:00:00Z",
    "is_active": true
  }
  ```

### `POST /sessions/end`
Ends the currently active tracking session for the user.
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):** Session details with `end_time` populated.

---

## 3. Analytics & Predictions

### `POST /predictions/metrics` (Tracker API)
Submits raw activity metrics to be evaluated by the ML model. Used internally by the Python Desktop Tracker.
* **Headers:** `Authorization: Bearer <token>`
* **Body:**
  ```json
  {
    "session_id": "uuid",
    "metrics": {
      "typing_speed": 45.2,
      "error_rate": 0.05,
      "mouse_speed": 120.5,
      ...
    }
  }
  ```

### `GET /analytics/summary`
Retrieves a high-level summary of the user's fatigue metrics for the dashboard.
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "current_fatigue_score": 0.34,
    "daily_average": 0.45,
    "weekly_trend": "decreasing"
  }
  ```

---

## 4. Admin API

**Note:** All endpoints under `/admin` require the user to have the `admin` role.

### `GET /admin/users`
Retrieves a paginated list of all users in the system.
* **Query Params:** `page` (int), `page_size` (int)
* **Response (200 OK):**
  ```json
  {
    "total": 150,
    "page": 1,
    "users": [ ... ]
  }
  ```

### `GET /admin/stats`
Retrieves platform-wide statistics for the admin dashboard.

### `GET /admin/export/csv`
Exports the entire fatigue metrics database as a streaming CSV file.

### `GET /admin/export/pdf`
Exports a high-level summary report as a dynamically generated PDF file.

---

## 5. WebSocket (Real-Time Notifications)

### `WS /ws/{user_id}?token={token}`
Establishes a persistent WebSocket connection to receive real-time fatigue alerts.

* **Client Message (Optional Ping):**
  ```json
  { "type": "ping" }
  ```
* **Server Message (Fatigue Alert):**
  ```json
  {
    "type": "fatigue_alert",
    "level": "high",
    "score": 0.85,
    "timestamp": "2026-07-14T10:15:00Z"
  }
  ```
