"""Learning endpoints (spec §18). Harness failures never leak to the student (spec §25)."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.deps import curriculum_dep, harness_dep
from curriculum.loader import Curriculum
from database.session import get_db
from harness.orchestrator import PedagogicalHarness
from schemas.api import (
    ReplyRequest,
    ReplyResponse,
    SafeError,
    SessionResponse,
    StartSessionRequest,
    SubmitRequest,
    SubmitResponse,
    TransferRequest,
    TransferResponse,
)
from services import learning
from services.students import NotFound

log = logging.getLogger("curio.api")
router = APIRouter(prefix="/api/learning", tags=["learning"])


def _safe(exc: Exception) -> JSONResponse:
    log.exception("harness failure: %s", exc)
    return JSONResponse(status_code=503, content=SafeError().model_dump())


@router.post("/sessions", response_model=SessionResponse)
def start_session(req: StartSessionRequest, db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    try:
        return learning.start_session(db, cur, req.student_id, req.topic_id, req.size)
    except NotFound as e:
        raise HTTPException(404, str(e))
    except learning.ContentNotReviewed as e:
        raise HTTPException(409, f"{e} Ask your teacher to review this topic first.")


@router.post("/submit", response_model=SubmitResponse, responses={503: {"model": SafeError}})
async def submit(req: SubmitRequest, db: Session = Depends(get_db), h: PedagogicalHarness = Depends(harness_dep)):
    if not req.answer.strip():
        raise HTTPException(422, "Please write an answer first.")
    try:
        return await learning.submit(db, h, req.student_id, req.question_id, req.answer, req.session_id)
    except NotFound as e:
        raise HTTPException(404, str(e))
    except Exception as e:  # noqa: BLE001 — spec §25: deterministic, friendly fallback
        db.rollback()
        return _safe(e)


@router.post("/reply", response_model=ReplyResponse, responses={503: {"model": SafeError}})
async def reply(req: ReplyRequest, db: Session = Depends(get_db), h: PedagogicalHarness = Depends(harness_dep)):
    try:
        return await learning.reply(db, h, req.student_id, req.interaction_id, req.message)
    except NotFound as e:
        raise HTTPException(404, str(e))
    except Exception as e:  # noqa: BLE001
        db.rollback()
        return _safe(e)


@router.post("/transfer", response_model=TransferResponse, responses={503: {"model": SafeError}})
async def transfer(req: TransferRequest, db: Session = Depends(get_db), h: PedagogicalHarness = Depends(harness_dep)):
    try:
        return await learning.transfer(db, h, req.student_id, req.interaction_id, req.answer)
    except NotFound as e:
        raise HTTPException(404, str(e))
    except Exception as e:  # noqa: BLE001
        db.rollback()
        return _safe(e)
