# Curio — common commands. Requires: uv (Python 3.11+), Node 20+ / npm.
.PHONY: setup dev backend frontend test check seed fixtures build eval eval-llm-baseline video video-short
NODE ?= $(if $(CURIO_NODE_BIN),$(CURIO_NODE_BIN),node)

setup:            ## install backend + frontend dependencies
	cd backend && uv sync --group dev
	cd frontend && npm install

dev:              ## run backend (:8000, or CURIO_API_PORT) and frontend (:3000) together
	./scripts/dev.sh

backend:          ## FastAPI with reload
	cd backend && uv run uvicorn main:app --reload --port $${CURIO_API_PORT:-8000}

frontend:         ## Next.js dev server
	cd frontend && "$(NODE)" node_modules/next/dist/bin/next dev -p $${CURIO_WEB_PORT:-3000}

test:             ## backend tests + curriculum lint + frontend typecheck
	cd backend && uv run pytest -q
	cd backend && uv run python scripts/check_curriculum.py
	cd frontend && "$(NODE)" node_modules/typescript/bin/tsc --noEmit

check: test       ## alias

seed:             ## rebuild the demo database (Alex + class of 24)
	cd backend && uv run python -m database.seed --force

eval:             ## run the gold-labelled benchmark → backend/evaluation/reports/latest.{json,md}
	cd backend && uv run python -m evaluation.run

eval-llm-baseline: ## "why not just prompt an LLM?": one-prompt LLM vs Curio → reports/llm_only.{json,md} (needs CURIO_LLM_* in backend/.env)
	cd backend && uv run python -m evaluation.llm_only --with-curio-llm

fixtures:         ## regenerate offline-demo fixtures from the real backend
	cd backend && uv run python scripts/export_fixtures.py

build:            ## production build of the frontend
	cd frontend && "$(NODE)" node_modules/next/dist/bin/next build

video:            ## record docs/demo/curio_demo.mp4 (needs backend :8000 + frontend :3000 running, ffmpeg)
	cd backend && uv run python -m database.seed --force
	env -u VIRTUAL_ENV uv run --no-project --with playwright==1.48.0 python scripts/record_demo.py

video-short:      ## record the ~1 minute cut → docs/demo/curio_demo_1min.mp4
	cd backend && uv run python -m database.seed --force
	env -u VIRTUAL_ENV uv run --no-project --with playwright==1.48.0 python scripts/record_demo.py --short
