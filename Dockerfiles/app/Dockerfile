# uv 공식 이미지 베이스 (curl로 별도 설치 불필요, 버전 고정)
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

# 파이썬 환경 설정
# 로그 실시간 출력
ENV PYTHONUNBUFFERED=1
# .pyc 파일 생성 안 함
ENV PYTHONDONTWRITEBYTECODE=1
# venv 없이 시스템에 직접 설치. 컨테이너 자체가 격리된 환경이라 시스템에 직접 깔아도 문제없음
ENV UV_SYSTEM_PYTHON=1
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 빌드 도구가 필요한 경우에만 설치 (C 확장 없으면 이 블록 제거 가능)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 먼저 복사 (캐싱 활용)
COPY pyproject.toml uv.lock ./

# BuildKit 캐시 마운트로 uv sync 캐시
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --all-packages --no-dev

# 의존성 레이어 이후 → 코드 변경이 의존성 캐시에 영향 없음
COPY ./app ./app
COPY ./scripts/init-db ./scripts/init-db

# 스크립트 실행 권한 부여
#COPY ./scripts/entrypoint.sh ./scripts/entrypoint.sh
#RUN chmod +x /app/scripts/entrypoint.sh
# non-root 유저 생성 (보안)

# non-root 유저로 전환 (이후 프로세스는 app-user 권한으로 실행)
RUN adduser --disabled-password --no-create-home app-user
USER app-user

#EXPOSE 8000
#CMD ["/scripts/entrypoint.sh"]

# 컨테이너 시작 시 실행
#ENTRYPOINT ["/bin/bash", "/app/scripts/entrypoint.sh"]
# 서버 실행 (uvicorn이 시스템 경로에 바로 설치됨)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
