#
# Missing schemas: UserResponse and UserUpdateRequest
#
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: str
    role: str
    department: Optional[str] = None
    job_title: Optional[str] = None
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str
    role: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = None


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    fatigue_threshold: Optional[float] = None
    notification_preferences: Optional[dict] = None
