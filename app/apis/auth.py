import httpx
import secrets
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core import config
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# 네이버 OAuth 엔드포인트 상수
NAVER_AUTH_URL = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_PROFILE_URL = "https://openapi.naver.com/v1/nid/me"


# ① 로그인 시작 — 네이버 인증 페이지로 리다이렉트
@router.get("/naver/login")
async def naver_login():
    state = secrets.token_urlsafe(16)  # CSRF 방지용 랜덤 state

    params = {
        "response_type": "code",
        "client_id": config.NAVER_CLIENT_ID,
        "redirect_uri": config.NAVER_REDIRECT_URI,
        "state": state,
    }

    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    naver_url = f"{NAVER_AUTH_URL}?{query_string}"

    return {"login_url": naver_url}
    # return RedirectResponse(url=naver_url)


# ② 콜백 — 네이버가 code와 state를 들고 여기로 돌아옴
@router.get("/naver/callback", response_model=TokenResponse)
async def naver_callback(code: str, state: str):
    # Step 1: code → access_token 교환
    naver_token = await _get_naver_token(code, state)

    # Step 2: access_token → 사용자 프로필 조회
    profile = await _get_naver_profile(naver_token)

    # Step 3: DB에 유저 upsert (있으면 업데이트, 없으면 생성)
    user = await _get_or_create_user(profile)

    # Step 4: 우리 서비스 JWT 발급
    access_token = create_access_token(data={"sub": str(user.id)})

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

    data = response.json()

    if "access_token" not in data:
        raise HTTPException(
            status_code=400,
            detail=f"네이버 토큰 발급 실패: {data.get('error_description', 'unknown error')}"
        )

    return data["access_token"]


async def _get_naver_profile(access_token: str) -> dict:
    """네이버 프로필 API 호출"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            NAVER_PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    data = response.json()

    if data.get("resultcode") != "00":
        raise HTTPException(
            status_code=400,
            detail=f"네이버 프로필 조회 실패: {data.get('message', 'unknown error')}"
        )

    return data["response"]  # id, email, nickname, profile_image 포함


async def _get_or_create_user(profile: dict) -> User:
    """DB에서 유저 찾거나 새로 생성"""
    naver_id = profile["id"]

    user = await User.get_or_none(naver_id=naver_id)

    if user is None:
        # 신규 유저 생성
        user = await User.create(
            naver_id=naver_id,
            name=profile.get("name"),
            email=profile.get("email"),
            nickname=profile.get("nickname"),
            gender=profile.get("gender"),  # "M", "F", "U" 중 하나
            birthday=profile.get("birthday"),  # "10-22" 형식
            birthyear=profile.get("birthyear"),  # "1995" 형식
            profile_image=profile.get("profile_image"),
        )
    else:
        # 기존 유저 정보 업데이트 (닉네임/프사 변경 반영)
        user.name = profile.get("name", user.name)
        user.email = profile.get("email", user.email)
        user.nickname = profile.get("nickname", user.nickname)
        user.gender = profile.get("gender", user.gender)
        user.birthday = profile.get("birthday", user.birthday)
        user.birthyear = profile.get("birthyear", user.birthyear)
        user.profile_image = profile.get("profile_image", user.profile_image)
        await user.save()

    return user
