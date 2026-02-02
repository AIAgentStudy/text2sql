"""
JWT 토큰 생성 및 검증

Access Token: 30분 만료
Refresh Token: 7일 만료
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import get_settings


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Access Token 생성

    Args:
        data: 토큰에 포함할 데이터 (subject, roles 등)
        expires_delta: 만료 시간 (기본값: 30분)

    Returns:
        JWT Access Token
    """
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Refresh Token 생성

    Args:
        data: 토큰에 포함할 데이터 (subject)
        expires_delta: 만료 시간 (기본값: 7일)

    Returns:
        JWT Refresh Token
    """
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
    """
    토큰 검증

    Args:
        token: JWT 토큰
        token_type: 토큰 타입 ("access" 또는 "refresh")

    Returns:
        토큰 페이로드 (유효하지 않으면 None)
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # 토큰 타입 확인
        if payload.get("type") != token_type:
            return None

        return payload

    except JWTError:
        return None


def decode_token_without_verification(token: str) -> dict[str, Any] | None:
    """
    토큰 검증 없이 디코딩 (디버깅용)

    Args:
        token: JWT 토큰

    Returns:
        토큰 페이로드
    """
    try:
        return jwt.get_unverified_claims(token)
    except JWTError:
        return None
