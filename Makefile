# Curio — common commands. Requires: uv (Python 3.11+), Node 20+ / npm.
.PHONY: setup dev backend frontend test check seed fixtures build eval video video-short

setup:            ## install backend + frontend dependencies
	cd backend && uv sync --group dev
	cd frontend && npm install

dev:              ## run backend (:8000) and frontend (:3000) together
	./scripts/dev.sh

backend:          ## FastAPI with reload
	cd backend && uv run uvicorn main:app --reload --port 8000

frontend:         ## Next.js dev server
	cd frontend && npm run dev

test:             ## backend tests + curriculum lint + frontend typecheck
	cd backend && uv run pytest -q
	cd backend && uv run python scripts/check_curriculum.py
	cd frontend && npx tsc --noEmit

check: test       ## alias

seed:             ## rebuild the demo database (Alex + class of 24)
	cd backend && uv run python -m database.seed --force

eval:             ## run the gold-labelled benchmark → backend/evaluation/reports/latest.{json,md}
	cd backend && uv run python -m evaluation.run

fixtures:         ## regenerate offline-demo fixtures from the real backend
	cd backend && uv run python scripts/export_fixtures.py

build:            ## production build of the frontend
	cd frontend && npm run build

video:            ## record docs/demo/curio_demo.mp4 (needs backend :8000 + frontend :3000 running, ffmpeg)
	cd backend && uv run python -m database.seed --force
	env -u VIRTUAL_ENV uv run --no-project --with playwright==1.48.0 python scripts/record_demo.py

video-short:      ## record the ~1 minute cut → docs/demo/curio_demo_1min.mp4
	cd backend && uv run python -m database.seed --force
	env -u VIRTUAL_ENV uv run --no-project --with playwright==1.48.0 python scripts/record_demo.py --short
