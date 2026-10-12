from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import curriculum_dep
from curriculum.loader import Curriculum
from database.session import get_db
from schemas.api import ClassAnalytics, TraceDetail, TraceSummary
from services import analytics
from services.students import NotFound

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/class", response_model=ClassAnalytics)
def class_overview(class_name: str | None = None, db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    return analytics.class_analytics(db, cur, class_name)


@router.get("/traces", response_model=list[TraceSummary])
def traces(limit: int = 30, student_id: str | None = None, db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    return analytics.list_traces(db, cur, min(limit, 200), student_id)


@router.get("/traces/{trace_id}", response_model=TraceDetail)
def trace(trace_id: str, db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    try:
        return analytics.trace_detail(db, cur, trace_id)
    except NotFound:
        raise HTTPException(404, "Trace not found")
