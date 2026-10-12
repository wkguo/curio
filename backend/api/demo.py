from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config import get_settings
from database.seed import reset_demo_student, seed
from database.session import get_db
from services.llm import get_llm

router = APIRouter(prefix="/api", tags=["demo"])


@router.get("/health")
def health():
    s = get_settings()
    llm = get_llm()
    return {"status": "ok", "harness_mode": s.harness_mode, "llm": llm.name, "llm_available": llm.available, "model": s.llm_model if llm.available else None}


@router.post("/demo/reset")
def reset_demo(db: Session = Depends(get_db)):
    """One-click reset of the demo student (spec §21)."""
    reset_demo_student(db)
    return {"ok": True, "student_id": "demo_student"}


@router.post("/demo/reseed")
def reseed():
    """Rebuild ALL demo data, including the synthetic class."""
    seed(force=True)
    return {"ok": True}
