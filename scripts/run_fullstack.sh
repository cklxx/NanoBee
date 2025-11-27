#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ensure_env_file() {
  local target=$1
  local example=$2

  if [[ ! -f "$target" && -f "$example" ]]; then
    echo "[run_fullstack] ${target} not found, copying from ${example}"
    cp "$example" "$target"
  fi
}

ensure_backend_dependencies() {
  if python3 -m pip show nanobee-backend >/dev/null 2>&1; then
    return
  fi

  echo "[run_fullstack] Installing backend dependencies (editable mode)"
  python3 -m pip install -e backend
}

ensure_env_file ".env" ".env.example"
ensure_env_file "frontend/.env" "frontend/.env.example"

ensure_backend_dependencies

if [[ -f .env ]]; then
  echo "[run_fullstack] Loading environment from .env"
  set -a
  source .env
  set +a
fi

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
API_BASE=${NEXT_PUBLIC_API_BASE:-http://localhost:${BACKEND_PORT}}

export NEXT_PUBLIC_API_BASE="$API_BASE"

# Launch backend
echo "[run_fullstack] Starting backend on port ${BACKEND_PORT}"
uvicorn backend.app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

cleanup() {
  echo "[run_fullstack] Shutting down backend (pid=${BACKEND_PID})"
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

# Install frontend deps if missing
if [[ ! -d frontend/node_modules ]]; then
  echo "[run_fullstack] Installing frontend dependencies"
  (cd frontend && npm install)
fi

# Start frontend dev server
echo "[run_fullstack] Starting frontend on port ${FRONTEND_PORT} (API base: ${API_BASE})"
cd frontend
npm run dev -- --hostname 0.0.0.0 --port "$FRONTEND_PORT"
