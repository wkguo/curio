#!/usr/bin/env bash
# Start the Curio backend and frontend together; Ctrl+C stops both.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Use another backend port if 8000 is taken: CURIO_API_PORT=8765 make dev
PORT="${CURIO_API_PORT:-8000}"
# Bind test (never connects to whatever is already listening there).
if ! python3 -c "import socket,sys; socket.socket().bind(('127.0.0.1', int(sys.argv[1])))" "$PORT" 2>/dev/null; then
  echo "Port $PORT is already in use; the frontend would proxy /api to that service. Set CURIO_API_PORT." >&2
  exit 1
fi
export CURIO_API_URL="http://127.0.0.1:$PORT"

(cd "$ROOT/backend" && uv run uvicorn main:app --reload --port "$PORT") &
BACK=$!
(cd "$ROOT/frontend" && npm run dev) &
FRONT=$!
trap 'kill $BACK $FRONT 2>/dev/null' INT TERM EXIT
echo "Curio → http://localhost:3000   (API docs → http://localhost:$PORT/docs)"
wait
