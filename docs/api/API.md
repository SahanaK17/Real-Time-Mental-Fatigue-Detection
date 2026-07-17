# API Reference

**Base URL:** `http://<host>:<port>/api/v1`

All REST endpoints are versioned under `/api/v1`. Authentication is performed via JSON Web Tokens (JWT) passed in the `Authorization` header.

```http
Authorization: Bearer <access_token>
```

---

**Navigation:** [← Back to README](../../README.md) | [Architecture](../architecture/ARCHITECTURE.md) | [Deployment](../deployment/DEPLOYMENT.md) | [Developer Guide](../developer/DEVELOPER_GUIDE.md)

---

## Table of Contents

- [Authentication](#1-authentication)
- [Session Management](#2-session-management)
- [Behaviour Ingestion](#3-behaviour-ingestion)
- [Analytics & Predictions](#4-analytics--predictions)
- [Recommendations](#5-recommendations)
- [Notifications](#6-notifications)
- [Admin](#7-admin)
- [WebSocket](#8-websocket)

---

## 1. Authentication

### `POST /auth/signup`

Creates a new user account.

**Request Body:**
```json
{
  "email": "user@company.com",
  "username": "john.doe",
  "password": "SecurePassword123",
  "full_name": "John Doe",
  "department": "Engineering",
  "job_title": "Software Engineer"
}
```

**Response `201 Created`:**
```json
{
  "id": "c18bdb44-562a-4ad5-b3ee-0ff4792f600f",
  "email": "user@company.com",
  "username": "john.doe",
  "full_name": "John Doe",
  "role": "employee",
  "is_active": true,
  "is_verified": false
}
```

---

### `POST /auth/login`

Authenticates a user using `application/x-www-form-urlencoded` format (OAuth2 Password Flow).

**Request Body (form-encoded):**
```
username=user@company.com&password=SecurePassword123
```

**Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { "id": "...", "email": "...", "role": "employee" }
}
```

---

### `POST /auth/refresh`

Exchanges a valid refresh token for a new access token.

**Request Body:**
```json
{ "refresh_token": "<refresh_token>" }
```

---

### `POST /auth/logout`

Revokes the current access token by adding its JTI to the Redis blacklist.

**Headers:** `Authorization: Bearer <access_token>`

**Response:** `204 No Content`

---

### `GET /auth/me`

Returns the authenticated user's profile.

**Response `200 OK`:** User object (same schema as signup response).

---

## 2. Session Management

### `POST /sessions/start`

Starts a new tracking session for the authenticated user.

**Response `200 OK`:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "start_time": "2026-07-14T10:00:00Z",
  "is_active": true
}
```

---

### `POST /sessions/end`

Ends the currently active tracking session.

**Response `200 OK`:** Session object with `end_time` populated.

---

### `GET /sessions/active`

Returns the currently active session, if any.

---

## 3. Behaviour Ingestion

### `POST /behaviour/snapshot`

Submits a single 1-second aggregated behavioral feature window for ML inference. This is the primary endpoint called by the Desktop Tracker.

**Request Body:**
```json
{
  "session_id": "uuid",
  "timestamp": "2026-07-14T10:05:00Z",
  "typing_speed_wpm": 62.3,
  "key_hold_time_ms": 95.1,
  "flight_time_ms": 148.7,
  "error_rate": 0.03,
  "typing_rhythm_variance": 12.4,
  "mouse_speed_px_s": 410.2,
  "mouse_acceleration": 15.8,
  "direction_changes": 22,
  "click_frequency": 4.1
}
```

---

### `POST /behaviour/batch`

Submits multiple feature windows in a single request. Useful when the tracker has been offline and needs to sync buffered data.

**Request Body:** `{ "snapshots": [<snapshot>, ...] }`

---

## 4. Analytics & Predictions

### `GET /analytics/summary`

Returns aggregated fatigue statistics for the authenticated user's dashboard.

**Response `200 OK`:**
```json
{
  "current_fatigue_score": 0.34,
  "daily_average": 0.45,
  "peak_fatigue_score": 0.78,
  "total_sessions_today": 2,
  "weekly_trend": "decreasing"
}
```

---

### `GET /analytics/daily`

Returns an hourly fatigue trend for a given day.

**Query Params:** `target_date` (ISO date string, defaults to today)

---

### `GET /analytics/weekly`

Returns a daily fatigue trend for the past 7 days.

---

### `GET /analytics/heatmap`

Returns a day-of-week × hour-of-day fatigue intensity matrix.

**Query Params:** `days` (int, default 30)

---

### `GET /predictions/latest`

Returns the most recent fatigue prediction for the authenticated user.

---

### `GET /predictions/history`

Returns a paginated history of fatigue predictions.

**Query Params:** `page`, `page_size`, `session_id` (optional filter)

---

## 5. Recommendations

### `GET /recommendations/`

Returns active wellness recommendations for the user.

---

### `POST /recommendations/{id}/dismiss`

Dismisses a specific recommendation.

---

### `POST /recommendations/{id}/complete`

Marks a recommendation as completed.

---

## 6. Notifications

### `GET /notifications/`

Returns all notifications for the authenticated user.

**Query Params:** `unread_only` (boolean)

---

### `POST /notifications/{id}/read`

Marks a specific notification as read.

---

### `POST /notifications/read-all`

Marks all notifications as read.

---

## 7. Admin

> All endpoints under `/admin` require the `admin` role.

### `GET /admin/users`

Returns a paginated list of all users.

**Query Params:** `page`, `page_size`

---

### `GET /admin/stats`

Returns platform-wide aggregate statistics.

---

### `GET /admin/high-risk`

Returns users whose recent fatigue scores exceed a threshold.

**Query Params:** `threshold` (float, default `0.75`)

---

### `GET /admin/export/csv`

Streams the fatigue metrics database as a CSV file.

---

### `GET /admin/export/pdf`

Generates and returns a PDF summary report.

---

## 8. WebSocket

### `WS /ws/{user_id}?token={access_token}`

Establishes a persistent WebSocket connection for live fatigue telemetry. The server broadcasts fatigue events immediately after an ML inference exceeds the configured threshold.

**Authentication:** Pass the JWT access token as a query parameter. The connection is rejected with code `4001` (missing token) or `4003` (invalid/mismatched token) if authentication fails.

**Keepalive:**
```
Client → Server: "ping"
Server → Client: "pong"
```

**Event — Fatigue Alert:**
```json
{
  "type": "fatigue_update",
  "score": 0.85,
  "level": "high",
  "user_id": "uuid",
  "timestamp": "2026-07-14T10:15:00Z"
}
```

**Close Codes:**

| Code | Reason |
|:---|:---|
| `4001` | Missing authentication token |
| `4003` | Invalid or mismatched token |
| `1000` | Normal closure |
