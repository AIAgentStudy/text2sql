"""
인증 API 엔드포인트

회원가입, 로그인, 로그아웃, 토큰 갱신 기능을 제공합니다.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.dependencies import get_current_user, get_user_with_roles
from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.auth.password import hash_password, verify_password
from app.config import get_settings
from app.database.connection import get_connection
from app.models.auth import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserWithRoles,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["인증"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    description="새로운 사용자를 등록합니다. 기본 역할은 'viewer'입니다.",
)
async def register(request: RegisterRequest) -> UserResponse:
    """회원가입"""
    async with get_connection() as conn:
        # 이메일 중복 확인
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            request.email,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 등록된 이메일입니다",
            )

        # 비밀번호 해싱
        password_hash = hash_password(request.password)

        # 사용자 생성
        user_row = await conn.fetchrow(
            """
            INSERT INTO users (email, password_hash, name)
            VALUES ($1, $2, $3)
            RETURNING id, email, name, is_active, created_at
            """,
            request.email,
            password_hash,
            request.name,
        )

        user_id = user_row["id"]

        # 요청된 역할 할당
        selected_role = await conn.fetchrow(
            "SELECT id FROM roles WHERE name = $1",
            request.role,
        )
        if selected_role:
            await conn.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
                user_id,
                selected_role["id"],
            )

        logger.info(f"새 사용자 등록: {request.email}, 역할: {request.role}")

        return UserResponse(
            id=user_row["id"],
            email=user_row["email"],
            name=user_row["name"],
            is_active=user_row["is_active"],
            roles=[request.role],
            created_at=user_row["created_at"],
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="로그인",
    description="이메일과 비밀번호로 로그인합니다.",
)
async def login(request: LoginRequest, response: Response) -> TokenResponse:
    """로그인"""
    settings = get_settings()

    async with get_connection() as conn:
        # 사용자 조회
        user_row = await conn.fetchrow(
            """
            SELECT id, email, password_hash, name, is_active
            FROM users
            WHERE email = $1
            """,
            request.email,
        )

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다",
            )

        # 비밀번호 확인
        if not verify_password(request.password, user_row["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다",
            )

        # 계정 활성화 확인
        if not user_row["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다",
            )

        user_id = user_row["id"]

        # 역할 조회
        role_rows = await conn.fetch(
            """
            SELECT r.name
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = $1
            """,
            user_id,
        )
        roles = [row["name"] for row in role_rows]

    # 토큰 생성
    token_data = {"sub": user_id, "roles": roles}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user_id})

    # Refresh Token을 HttpOnly 쿠키로 설정
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,  # HTTPS에서만 전송 (개발 환경 제외)
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    logger.info(f"사용자 로그인: {request.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="로그아웃",
    description="현재 세션에서 로그아웃합니다.",
)
async def logout(
    response: Response,
    current_user: Annotated[UserWithRoles, Depends(get_current_user)],
) -> MessageResponse:
    """로그아웃"""
    # Refresh Token 쿠키 삭제
    response.delete_cookie(key="refresh_token")

    logger.info(f"사용자 로그아웃: {current_user.email}")

    return MessageResponse(message="로그아웃되었습니다")


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="토큰 갱신",
    description="Refresh Token으로 새로운 Access Token을 발급받습니다.",
)
async def refresh_token(
    request: RefreshRequest,
    response: Response,
) -> TokenResponse:
    """토큰 갱신"""
    settings = get_settings()

    # Refresh Token 검증
    payload = verify_token(request.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 Refresh Token입니다",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
        )

    # 사용자 정보 조회
    user = await get_user_with_roles(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다",
        )

    # 새 토큰 생성
    token_data = {"sub": user.id, "roles": user.roles}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token({"sub": user.id})

    # 새 Refresh Token을 쿠키로 설정
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    logger.info(f"토큰 갱신: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="현재 사용자 정보",
    description="현재 로그인한 사용자의 정보를 조회합니다.",
)
async def get_me(
    current_user: Annotated[UserWithRoles, Depends(get_current_user)],
) -> UserResponse:
    """현재 사용자 정보"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        is_active=current_user.is_active,
        roles=current_user.roles,
        created_at=current_user.created_at,
    )
