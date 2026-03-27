#!/bin/bash
set -e

echo "🚀 컨테이너 시작..."

echo "⏳ DB 연결 대기 중..."

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
MAX_RETRIES=30
RETRY_INTERVAL=2

for i in $(seq 1 $MAX_RETRIES); do
    # bash 내장 /dev/tcp 로 포트 열림 여부 확인
    # /dev/tcp 로 TCP 핸드셰이크만 확인 (netcat 불필요)
    if (echo > /dev/tcp/$DB_HOST/$DB_PORT) 2>/dev/null; then
        echo "✅ DB 연결 확인 (${DB_HOST}:${DB_PORT})"
        break
    fi

    echo "  [$i/$MAX_RETRIES] DB 미응답, ${RETRY_INTERVAL}초 후 재시도..."
    sleep $RETRY_INTERVAL

    # 최대 재시도 초과 시 강제 종료
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "❌ DB 연결 실패 — 컨테이너를 종료합니다."
        exit 1
    fi
done

echo "📦 Aerich 마이그레이션 실행..."
uv run aerich upgrade  # 이미 최신이면 "No upgrade needed" 출력 후 통과
echo "✅ 마이그레이션 완료"

# --------------------------------------------------------------
# Gunicorn + Uvicorn worker 로 서버 기동
#   - exec: 현재 셸 프로세스를 gunicorn 으로 교체
#     → PID 1 = gunicorn (Docker SIGTERM 이 직접 전달됨)
#   - -k uvicorn.workers.UvicornWorker: ASGI 지원
#   - --workers: CPU 코어 수 기반, 환경변수로 외부 주입 가능
#   - --bind 0.0.0.0:8000: 컨테이너 외부 노출
#   - --access-logfile -: 액세스 로그를 stdout 으로 출력
#   - --error-logfile -: 에러 로그를 stderr 로 출력
#   - --log-level: 환경변수로 조정 가능 (기본 info)
# --------------------------------------------------------------
echo "🌐 Gunicorn 서버 시작..."

exec uv run gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "${GUNICORN_WORKERS:-2}" \
    --bind "0.0.0.0:${APP_PORT:-8000}" \
    --access-logfile - \
    --error-logfile - \
    --log-level "${LOG_LEVEL:-info}"
