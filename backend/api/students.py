from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import curriculum_dep
from curriculum.loader import Curriculum
from database.session import get_db
from models.tables import Student
from schemas.api import DashboardResponse, StudentMasteryResponse, StudentProfile
from services import students as student_svc
from services.students import NotFound

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("", response_model=list[StudentProfile])
def list_students(db: Session = Depends(get_db)):
    return [student_svc.profile(s) for s in db.scalars(select(Student).order_by(Student.is_demo.desc(), Student.display_name)).all()]


@router.get("/{student_id}", response_model=StudentProfile)
def get_student(student_id: str, db: Session = Depends(get_db)):
    try:
        return student_svc.profile(student_svc.get_student(db, student_id))
    except NotFound:
        raise HTTPException(404, "Student not found")


@router.get("/{student_id}/mastery", response_model=StudentMasteryResponse)
def get_mastery(student_id: str, db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    try:
        return student_svc.student_mastery(db, cur, student_id)
    except NotFound:
        raise HTTPException(404, "Student not found")


@router.get("/{student_id}/dashboard", response_model=DashboardResponse)
def get_dashboard(student_id: str, db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    try:
        return student_svc.dashboard(db, cur, student_id)
    except NotFound:
        raise HTTPException(404, "Student not found")
