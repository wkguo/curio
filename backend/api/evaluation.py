import json

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from evaluation.run import REPORTS, run_and_save
from schemas.api import LLMComparisonReport

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


@router.get("/llm-baseline", response_model=LLMComparisonReport)
def llm_baseline():
    path = REPORTS / "llm_only.json"
    if not path.exists():
        return LLMComparisonReport()
    # Publish aggregate metrics, never the per-case student text or gold labels.
    return LLMComparisonReport.model_validate({**json.loads(path.read_text()), "available": True})


@router.get("/report")
def latest_report():
    path = REPORTS / "latest.json"
    if not path.exists():
        raise HTTPException(404, "No report yet — run the benchmark first.")
    return json.loads(path.read_text())


@router.post("/run")
async def run_benchmark(mode: str = "rules"):
    """Re-run the benchmark (rules mode is deterministic and takes ~1s)."""
    if mode not in ("rules", "llm"):
        raise HTTPException(422, "mode must be rules or llm")
    return await run_in_threadpool(run_and_save, mode)
