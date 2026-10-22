#!/usr/bin/env bash
# Start the Curio backend and frontend together; Ctrl+C stops both.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Use another backend port if 8000 is taken: CURIO_API_PORT=8765 make dev
PORT="${CURIO_API_PORT:-8000}"
WEB_PORT="${CURIO_WEB_PORT:-3000}"
NODE="${CURIO_NODE_BIN:-node}"
if ! command -v "$NODE" >/dev/null; then
  echo "Node.js was not found. Set CURIO_NODE_BIN to an installed Node.js executable." >&2
  exit 1
fi
# Bind test (never connects to whatever is already listening there).
if ! python3 -c "import socket,sys; socket.socket().bind(('127.0.0.1', int(sys.argv[1])))" "$PORT" 2>/dev/null; then
  echo "Port $PORT is already in use; the frontend would proxy /api to that service. Set CURIO_API_PORT." >&2
  exit 1
fi
if ! python3 -c "import socket,sys; socket.socket().bind(('127.0.0.1', int(sys.argv[1])))" "$WEB_PORT" 2>/dev/null; then
  echo "Port $WEB_PORT is already in use. Set CURIO_WEB_PORT." >&2
  exit 1
fi
export CURIO_API_URL="http://127.0.0.1:$PORT"
export CURIO_CORS_ORIGINS="http://localhost:$WEB_PORT,http://127.0.0.1:$WEB_PORT"

(cd "$ROOT/backend" && exec uv run uvicorn main:app --reload --host 127.0.0.1 --port "$PORT") &
BACK=$!
(cd "$ROOT/frontend" && exec "$NODE" node_modules/next/dist/bin/next dev --hostname 127.0.0.1 -p "$WEB_PORT") &
FRONT=$!
trap 'kill $BACK $FRONT 2>/dev/null' INT TERM EXIT
echo "Curio → http://localhost:$WEB_PORT   (API docs → http://localhost:$PORT/docs)"
wait -n "$BACK" "$FRONT"
