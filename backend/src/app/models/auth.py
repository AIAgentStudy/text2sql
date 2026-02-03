"""
인증 관련 Pydantic 모델
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# === 요청 모델 ===

class RegisterRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, description="비밀번호 (최소 8자)")
    name: str = Field(..., min_length=2, max_length=100, description="이름")
    role: Literal["viewer", "manager"] = Field(
        default="viewer",
        description="역할 (viewer: 조회자, manager: 매니저)"
    )


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., description="비밀번호")


class RefreshRequest(BaseModel):
    """토큰 갱신 요청 (쿠키 우선, body fallback)"""
    refresh_token: Optional[str] = Field(None, description="Refresh Token (쿠키 없을 때 fallback)")


# === 응답 모델 ===

class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str = Field(..., description="Access Token")
    refresh_token: str = Field(..., description="Refresh Token")
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(..., description="Access Token 만료 시간 (초)")


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: int
    email: str
    name: str
    is_active: bool
    roles: list[str]
    created_at: datetime


class MessageResponse(BaseModel):
    """일반 메시지 응답"""
    message: str


# === 내부 모델 ===

class TokenPayload(BaseModel):
    """JWT 토큰 페이로드"""
    sub: int = Field(..., description="사용자 ID")
    roles: list[str] = Field(default_factory=list, description="사용자 역할")
    type: Literal["access", "refresh"] = Field(..., description="토큰 타입")
    exp: datetime = Field(..., description="만료 시간")
    iat: datetime = Field(..., description="발급 시간")


class UserWithRoles(BaseModel):
    """역할 정보가 포함된 사용자"""
    id: int
    email: str
    name: str
    is_active: bool
    roles: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(BaseModel):
    """데이터베이스에 저장된 사용자"""
    id: int
    email: str
    password_hash: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
