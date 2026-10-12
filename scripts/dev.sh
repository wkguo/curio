#!/usr/bin/env bash
# Start the Curio backend and frontend together; Ctrl+C stops both.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

(cd "$ROOT/backend" && uv run uvicorn main:app --reload --port 8000) &
BACK=$!
(cd "$ROOT/frontend" && npm run dev) &
FRONT=$!
trap 'kill $BACK $FRONT 2>/dev/null' INT TERM EXIT
echo "Curio → http://localhost:3000   (API docs → http://localhost:8000/docs)"
wait
