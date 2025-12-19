#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ensure_env_file() {
  local target=$1
  local example=$2

  if [[ ! -f "$target" && -f "$example" ]]; then
    echo "[start_app] ${target} not found, copying from ${example}"
    cp "$example" "$target"
  fi
}

install_backend() {
  if [[ "${SKIP_BACKEND_INSTALL:-0}" == "1" ]]; then
    echo "[start_app] Skipping backend dependency installation (SKIP_BACKEND_INSTALL=1)"
    return
  fi

  echo "[start_app] Installing backend dependencies (editable mode, idempotent)"
  python3 -m pip install -e backend
}

install_frontend() {
  if [[ "${SKIP_FRONTEND_INSTALL:-0}" == "1" ]]; then
    echo "[start_app] Skipping frontend dependency installation (SKIP_FRONTEND_INSTALL=1)"
    return
  fi

  echo "[start_app] Installing frontend dependencies (idempotent)"
  (cd frontend && npm install)
}

ensure_env_file ".env" ".env.example"
ensure_env_file "frontend/.env" "frontend/.env.example"

install_backend
install_frontend

if [[ -f .env ]]; then
  echo "[start_app] Loading environment from .env"
  set -a
  source .env
  set +a
fi

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
API_BASE=${NEXT_PUBLIC_API_BASE:-http://localhost:${BACKEND_PORT}}

export NEXT_PUBLIC_API_BASE="$API_BASE"

start_backend() {
  echo "[start_app] Starting backend on port ${BACKEND_PORT}"
  python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &
  BACKEND_PID=$!
}

start_frontend() {
  echo "[start_app] Starting frontend on port ${FRONTEND_PORT} (API base: ${API_BASE})"
  (cd frontend && npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT") &
  FRONTEND_PID=$!
}

shutdown() {
  local code=${1:-0}
  echo "[start_app] Shutting down services"
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi
  wait >/dev/null 2>&1 || true
  exit "$code"
}

trap 'shutdown 130' INT TERM

start_backend
start_frontend

wait -n || true
shutdown
