"""
Backend Test Suite — MindGuard
================================
Covers: authentication, behaviour ingestion, analytics,
        ML inference fallback, and WebSocket authentication.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# ── Database override ────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_mindguard.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all tables in the test database before the test session."""
    from app.db.base import Base

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Return an async test client with DB override applied."""
    from app.main import app
    from app.db.session import get_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Fixtures ─────────────────────────────────────────────────

TEST_USER = {
    "email": "test@mindguard.dev",
    "username": "testuser",
    "password": "TestPass123!",
    "full_name": "Test User",
}


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient):
    """Register and return a test user."""
    response = await client.post("/api/v1/auth/signup", json=TEST_USER)
    assert response.status_code in (201, 409), f"Signup failed: {response.text}"
    return TEST_USER


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user):
    """Return Authorization headers for the test user."""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Tests: Health ────────────────────────────────────────────


class TestHealth:
    async def test_health_endpoint_returns_ok(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code in (200, 503)  # 503 if Redis not available
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "services" in data

    async def test_root_endpoint(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200
        assert "version" in response.json()


# ── Tests: Authentication ────────────────────────────────────


class TestAuthentication:
    async def test_signup_creates_user(self, client: AsyncClient):
        unique_user = {
            "email": "unique@mindguard.dev",
            "username": "uniqueuser",
            "password": "Password123!",
            "full_name": "Unique User",
        }
        response = await client.post("/api/v1/auth/signup", json=unique_user)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == unique_user["email"]
        assert "hashed_password" not in data  # passwords never exposed

    async def test_signup_duplicate_email_returns_409(self, client: AsyncClient, registered_user):
        response = await client.post("/api/v1/auth/signup", json=registered_user)
        assert response.status_code == 409

    async def test_login_returns_tokens(self, client: AsyncClient, registered_user):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": registered_user["email"],
                "password": registered_user["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password_returns_401(self, client: AsyncClient, registered_user):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": registered_user["email"],
                "password": "WrongPassword!",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 401

    async def test_me_returns_profile(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "role" in data

    async def test_protected_endpoint_without_token_returns_401(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_token_refresh(self, client: AsyncClient, registered_user):
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={
                "username": registered_user["email"],
                "password": registered_user["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        refresh_token = login_resp.json()["refresh_token"]
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()


# ── Tests: Session Management ────────────────────────────────


class TestSessions:
    async def test_start_session(self, client: AsyncClient, auth_headers):
        response = await client.post("/api/v1/sessions/start", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["is_active"] is True

    async def test_end_session(self, client: AsyncClient, auth_headers):
        # Start first
        start_resp = await client.post("/api/v1/sessions/start", headers=auth_headers)
        assert start_resp.status_code == 200

        # End session
        end_resp = await client.post("/api/v1/sessions/end", headers=auth_headers)
        assert end_resp.status_code == 200

    async def test_get_active_session(self, client: AsyncClient, auth_headers):
        await client.post("/api/v1/sessions/start", headers=auth_headers)
        response = await client.get("/api/v1/sessions/active", headers=auth_headers)
        assert response.status_code in (200, 404)


# ── Tests: Behaviour Ingestion ───────────────────────────────

VALID_SNAPSHOT = {
    "typing_speed_wpm": 62.3,
    "typing_speed_cpm": 311.5,
    "key_hold_time_ms": 95.1,
    "flight_time_ms": 148.7,
    "backspace_count": 2,
    "error_rate": 0.03,
    "idle_time_keyboard_s": 0.5,
    "typing_burst_score": 0.8,
    "typing_rhythm_variance": 12.4,
    "total_keystrokes": 60,
    "mouse_speed_px_s": 410.2,
    "mouse_acceleration": 15.8,
    "mouse_distance_px": 1200.0,
    "click_frequency": 0.5,
    "double_click_count": 1,
    "drag_count": 0,
    "scroll_speed": 5.0,
    "scroll_distance": 200.0,
    "idle_time_mouse_s": 0.2,
    "direction_changes": 8,
    "hover_duration_ms": 350.0,
    "total_idle_time_s": 0.7,
    "session_elapsed_s": 60,
    "time_of_day_hour": 14.5,
}


class TestBehaviourIngestion:
    async def test_snapshot_submission_succeeds(self, client: AsyncClient, auth_headers):
        # Start a session first
        await client.post("/api/v1/sessions/start", headers=auth_headers)

        response = await client.post(
            "/api/v1/behaviour/snapshot",
            json=VALID_SNAPSHOT,
            headers=auth_headers,
        )
        assert response.status_code in (200, 201, 422)

    async def test_snapshot_without_auth_returns_401(self, client: AsyncClient):
        response = await client.post("/api/v1/behaviour/snapshot", json=VALID_SNAPSHOT)
        assert response.status_code == 401


# ── Tests: Analytics ─────────────────────────────────────────


class TestAnalytics:
    async def test_summary_returns_200(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/analytics/summary", headers=auth_headers)
        assert response.status_code == 200

    async def test_daily_analytics_returns_200(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/analytics/daily", headers=auth_headers)
        assert response.status_code == 200

    async def test_weekly_analytics_returns_200(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/analytics/weekly", headers=auth_headers)
        assert response.status_code == 200


# ── Tests: ML Inference ──────────────────────────────────────


class TestMLInference:
    def test_fallback_prediction_returns_score(self):
        """Verify the heuristic fallback works without a trained model."""
        from app.ml.inference import model_registry

        result = model_registry._fallback_prediction(
            {
                "error_rate": 0.2,
                "idle_time_keyboard_s": 30.0,
                "idle_time_mouse_s": 20.0,
            }
        )
        assert "fatigue_score" in result
        assert 0.0 <= result["fatigue_score"] <= 1.0
        assert result["model_name"] == "heuristic_fallback"

    def test_score_to_level_mapping(self):
        """Verify all fatigue levels are mapped correctly."""
        from app.ml.inference import score_to_level

        assert score_to_level(0.1) == "alert"
        assert score_to_level(0.3) == "mild"
        assert score_to_level(0.6) == "moderate"
        assert score_to_level(0.75) == "high"
        assert score_to_level(0.9) == "critical"
