"""Curio backend — FastAPI entrypoint.

    uv run uvicorn main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import analytics, curriculum, demo, evaluation, learning, privacy, students, teacher
from config import get_settings
from curriculum.loader import get_curriculum
from database.seed import seed
from database.session import SessionLocal
from services import privacy as privacy_svc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_curriculum()  # fail fast on an invalid curriculum pack
    seed(force=False)
    with SessionLocal() as db:  # data minimisation: records past the retention period go at every start
        privacy_svc.purge_expired(db)
    yield


app = FastAPI(
    title="Curio API",
    description="AI learning verification & teaching agent — Verify → Validate → Teach → Question Back → Confirm.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)
for r in (curriculum.router, students.router, learning.router, analytics.router, teacher.router, privacy.router, evaluation.router, demo.router):
    app.include_router(r)
