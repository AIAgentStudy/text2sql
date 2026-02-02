"""
FastAPI 인증 의존성

요청에서 현재 사용자를 추출하고 역할 기반 접근 제어를 수행합니다.
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import verify_token
from app.database.connection import get_connection
from app.models.auth import TokenPayload, UserWithRoles

logger = logging.getLogger(__name__)

# Bearer 토큰 스키마
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> UserWithRoles:
    """
    현재 인증된 사용자 가져오기

    Args:
        credentials: HTTP Bearer 토큰

    Returns:
        현재 사용자 정보 (역할 포함)

    Raises:
        HTTPException: 인증 실패 시
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = TokenPayload(**payload)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 페이로드가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 데이터베이스에서 사용자 정보 조회
    user = await get_user_with_roles(token_data.sub)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다",
        )

    return user


async def get_user_with_roles(user_id: int) -> UserWithRoles | None:
    """
    사용자 정보와 역할 조회

    Args:
        user_id: 사용자 ID

    Returns:
        사용자 정보 (역할 포함)
    """
    query = """
        SELECT
            u.id,
            u.email,
            u.name,
            u.is_active,
            u.created_at,
            COALESCE(
                array_agg(r.name) FILTER (WHERE r.name IS NOT NULL),
                ARRAY[]::varchar[]
            ) as roles
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE u.id = $1
        GROUP BY u.id, u.email, u.name, u.is_active, u.created_at
    """

    try:
        async with get_connection() as conn:
            row = await conn.fetchrow(query, user_id)

            if row is None:
                return None

            return UserWithRoles(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                roles=list(row["roles"]),
            )
    except Exception as e:
        logger.error(f"사용자 조회 실패: {e}")
        return None


def require_roles(allowed_roles: list[str]):
    """
    특정 역할이 필요한 엔드포인트를 위한 의존성 생성

    Args:
        allowed_roles: 허용된 역할 목록

    Returns:
        FastAPI 의존성 함수
    """
    async def role_checker(
        current_user: Annotated[UserWithRoles, Depends(get_current_user)],
    ) -> UserWithRoles:
        # admin은 모든 접근 허용
        if "admin" in current_user.roles:
            return current_user

        # 허용된 역할 중 하나라도 있으면 접근 허용
        if not any(role in current_user.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"이 작업을 수행할 권한이 없습니다. 필요한 역할: {', '.join(allowed_roles)}",
            )

        return current_user

    return role_checker


# 역할별 의존성 (편의를 위해 미리 정의)
require_admin = require_roles(["admin"])
require_manager = require_roles(["admin", "manager"])
require_viewer = require_roles(["admin", "manager", "viewer"])


async def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> UserWithRoles | None:
    """
    선택적 인증 (인증 없이도 접근 가능하지만, 인증 시 사용자 정보 제공)

    Args:
        credentials: HTTP Bearer 토큰 (선택)

    Returns:
        현재 사용자 정보 또는 None
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        return None

    try:
        token_data = TokenPayload(**payload)
        return await get_user_with_roles(token_data.sub)
    except Exception:
        return None
