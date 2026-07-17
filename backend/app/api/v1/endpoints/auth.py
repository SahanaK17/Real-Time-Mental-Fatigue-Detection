"""
Authentication API Endpoints
=============================
POST /auth/signup   — Register new user
POST /auth/login    — Login, get tokens
POST /auth/refresh  — Refresh access token
POST /auth/logout   — Revoke access token
GET  /auth/me       — Get current user profile
POST /auth/forgot-password — Send password reset email
POST /auth/reset-password  — Reset password with token
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.redis_client import redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from app.db.models import AuditLog, User, UserRole
from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


# ── Helpers ───────────────────────────────────────────────

async def _log_audit(
    db: AsyncSession,
    user_id: Optional[str],
    action: str,
    request: Request,
    success: bool = True,
    details: dict = None,
) -> None:
    """Create an audit log entry."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=details or {},
        success=success,
    )
    db.add(log)


# ── Endpoints ─────────────────────────────────────────────

@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def signup(
    payload: SignupRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user account.

    - **email**: Must be unique
    - **username**: Must be unique, 3-50 chars
    - **password**: Minimum 8 characters
    - **role**: Defaults to 'employee'
    """
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    if result.scalar_one_or_none():
        raise ConflictError("An account with this email already exists")

    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == payload.username.lower()))
    if result.scalar_one_or_none():
        raise ConflictError("Username is already taken")

    # Create user
    user = User(
        email=payload.email.lower(),
        username=payload.username.lower(),
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=UserRole(payload.role) if payload.role else UserRole.EMPLOYEE,
        department=payload.department,
        job_title=payload.job_title,
        notification_preferences={
            "browser": True,
            "email": False,
            "fatigue_threshold": 0.7,
        },
    )
    db.add(user)
    await db.flush()  # Get ID before commit

    await _log_audit(db, str(user.id), "signup", request, success=True)
    await db.commit()
    await db.refresh(user)

    logger.info("New user registered", user_id=str(user.id), email=user.email, role=user.role)

    return user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate and receive JWT tokens",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with email/username and password.
    Returns access token (30min) and refresh token (7 days).
    """
    # Support login with email or username
    identifier = form_data.username.lower()
    result = await db.execute(
        select(User).where(
            (User.email == identifier) | (User.username == identifier)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        await _log_audit(db, None, "login_failed", request, success=False, details={"identifier": identifier})
        await db.commit()
        raise AuthenticationError("Invalid credentials")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated. Contact your administrator.")

    # Generate tokens
    extra_claims = {
        "role": user.role.value,
        "email": user.email,
        "username": user.username,
    }
    access_token = create_access_token(str(user.id), extra_claims=extra_claims)
    refresh_token = create_refresh_token(str(user.id))

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await _log_audit(db, str(user.id), "login", request, success=True)
    await db.commit()

    logger.info("User logged in", user_id=str(user.id), email=user.email)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new access token.
    """
    token_payload = decode_refresh_token(payload.refresh_token)
    if not token_payload:
        raise AuthenticationError("Invalid or expired refresh token")

    user_id = token_payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")

    extra_claims = {"role": user.role.value, "email": user.email}
    new_access_token = create_access_token(str(user.id), extra_claims=extra_claims)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke current token",
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke the current access token by adding its JTI to the Redis blacklist.
    """
    # Extract JTI from Authorization header
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    from app.core.security import decode_access_token
    payload = decode_access_token(token)
    if payload and payload.get("jti"):
        # Blacklist until original expiry
        import time
        remaining = int(payload.get("exp", 0) - time.time())
        if remaining > 0:
            await redis_client.blacklist_token(payload["jti"], remaining)

    await _log_audit(db, str(current_user.id), "logout", request)
    await db.commit()

    logger.info("User logged out", user_id=str(current_user.id))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a password reset email",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a password reset link to the provided email.
    Always returns 202 to prevent email enumeration.
    """
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()

    if user:
        # Generate a short-lived reset token (15 minutes)
        reset_token = create_access_token(
            str(user.id),
            expires_delta=timedelta(minutes=15),
            extra_claims={"type": "password_reset"},
        )
        # Store in Redis
        await redis_client.set(
            f"reset_token:{str(user.id)}", reset_token, expire=900
        )
        # Send email in background (stub — configure SMTP in settings)
        logger.info("Password reset requested", user_id=str(user.id))
        # background_tasks.add_task(send_reset_email, user.email, reset_token)

    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password using the token from email",
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset the user's password using the token received by email.
    """
    from app.core.security import decode_access_token
    token_payload = decode_access_token(payload.token)

    if not token_payload or token_payload.get("type") != "access":
        raise AuthenticationError("Invalid or expired reset token")

    user_id = token_payload.get("sub")

    # Verify token matches stored one
    stored_token = await redis_client.get(f"reset_token:{user_id}")
    if not stored_token or stored_token != payload.token:
        raise AuthenticationError("Reset token has already been used or expired")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User", user_id)

    user.hashed_password = get_password_hash(payload.new_password)
    await redis_client.delete(f"reset_token:{user_id}")
    await db.commit()

    logger.info("Password reset successful", user_id=user_id)
    return {"message": "Password has been reset successfully. Please log in with your new password."}
