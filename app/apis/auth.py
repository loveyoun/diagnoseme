import secrets
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.core import config
from app.core.security import create_access_token, oauth2_scheme
from app.models.auth import AuthProvider, SocialAccount
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, UserSignin, SignUpRequest
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: SignUpRequest) -> UserResponse:
    return await AuthService.create(user_data)

@router.post("/signin", response_model=TokenResponse)
async def signin(user_data: UserSignin) -> TokenResponse:
    return await AuthService.signin(user_data)


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)) -> dict[str, str]:
    await AuthService.logout(token)
    return {"message": "Logged out successfully"}


# 네이버 OAuth 엔드포인트 상수
NAVER_AUTH_URL: str = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL: str = "https://nid.naver.com/oauth2.0/token"
NAVER_PROFILE_URL: str = "https://openapi.naver.com/v1/nid/me"


# 1. 로그인 시작 — 네이버 인증 페이지로 리다이렉트
@router.get("/naver/login")
async def naver_login() -> dict[str, str]:
    state: str = secrets.token_urlsafe(16)  # CSRF 방지용 랜덤 state

    params: dict[str, str] = {
        "response_type": "code",
        "client_id": config.NAVER_CLIENT_ID,
        "redirect_uri": config.NAVER_REDIRECT_URI,
        "state": state,
    }

    query_string: str = "&".join(f"{k}={v}" for k, v in params.items())
    naver_url: str = f"{NAVER_AUTH_URL}?{query_string}"

    return {"login_url": naver_url}


# 2. 콜백 — 네이버가 code와 state를 들고옴
@router.get("/naver/callback", response_model=TokenResponse)
async def naver_callback(code: str, state: str) -> TokenResponse:
    # Step 1: code → access_token 교환
    naver_token: str = await _get_naver_token(code, state)

    # Step 2: access_token → 사용자 프로필 조회
    profile: dict[str, Any] = await _get_naver_profile(naver_token)

    # Step 3: DB에 유저 및 소셜 계정 upsert
    user: User = await _get_or_create_user(profile)

    # Step 4: 우리 서비스 JWT 발급
    access_token: str = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token)


# ─── 내부 헬퍼 함수들 ───────────────────────────────────────

async def _get_naver_token(code: str, state: str) -> str:
    """네이버에서 액세스 토큰 받아오기"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            NAVER_TOKEN_URL,
            params={
                "grant_type": "authorization_code",
                "client_id": config.NAVER_CLIENT_ID,
                "client_secret": config.NAVER_CLIENT_SECRET,
                "code": code,
                "state": state,
            },
        )

    data: dict[str, Any] = response.json()

    if "access_token" not in data:
        raise HTTPException(
            status_code=400,
            detail=f"네이버 토큰 발급 실패: {data.get('error_description', 'unknown error')}"
        )

    return data["access_token"]


async def _get_naver_profile(access_token: str) -> dict[str, Any]:
    """네이버 프로필 API 호출"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            NAVER_PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    data: dict[str, Any] = response.json()

    if data.get("resultcode") != "00":
        raise HTTPException(
            status_code=400,
            detail=f"네이버 프로필 조회 실패: {data.get('message', 'unknown error')}"
        )

    return data["response"]  # id, email, nickname, profile_image 포함


async def _get_or_create_user(profile: dict[str, Any]) -> User:
    """DB에서 유저 찾거나 새로 생성 (SocialAccount 활용)"""
    external_id: str = profile["id"]
    provider, _ = await AuthProvider.get_or_create(code="naver")

    social_account = await SocialAccount.get_or_none(
        provider=provider,
        external_id=external_id
    ).select_related("user")

    if social_account:
        user: User = social_account.user
        # 기존 유저 정보 업데이트
        return await UserService.update_user(user.id, user)
    else:
        # 신규 유저 및 소셜 계정 생성
        # 기본 역할 설정 (예: 'user')
        role, _ = await UserRole.get_or_create(code="user")
        
        user = await User.create(
            name=profile.get("name"),
            email=profile.get("email"),
            nickname=profile.get("nickname"),
            gender=profile.get("gender"),
            birthday=profile.get("birthday"),
            birthyear=profile.get("birthyear"),
            profile_image=profile.get("profile_image"),
            role=role
        )
        await SocialAccount.create(
            user=user,
            provider=provider,
            external_id=external_id
        )

        return user
