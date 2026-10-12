from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.session import get_db
from schemas.api import PrivacySummary
from services import privacy
from services.students import NotFound, get_student

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.get("/students/{student_id}", response_model=PrivacySummary)
def summary(student_id: str, db: Session = Depends(get_db)):
    try:
        get_student(db, student_id)
    except NotFound:
        raise HTTPException(404, "Student not found")
    return privacy.summary(db, student_id)


@router.delete("/students/{student_id}")
def delete_data(student_id: str, db: Session = Depends(get_db)):
    """Delete a student's learning records (the demo student is restored by /api/demo/reset)."""
    try:
        get_student(db, student_id)
    except NotFound:
        raise HTTPException(404, "Student not found")
    return {"ok": True, "deleted": privacy.delete_learning_data(db, student_id)}


@router.post("/purge")
def purge(db: Session = Depends(get_db)):
    return {"ok": True, "deleted": privacy.purge_expired(db)}
