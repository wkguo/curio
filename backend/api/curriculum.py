from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import curriculum_dep
from curriculum.loader import Curriculum
from database.session import get_db
from schemas.api import TopicDetail, TopicSummary
from services import students as student_svc

router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])


@router.get("/topics", response_model=list[TopicSummary])
def list_topics(student_id: str | None = None, db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    rows = student_svc.mastery_rows(db, student_id) if student_id else None
    out = []
    for t in cur.topics:
        mastery = None
        if rows is not None:
            mastery = student_svc.topic_progress(t, student_svc.concept_nodes(cur, t, rows)).mastery
        out.append(student_svc.topic_summary(t, mastery))
    return out


@router.get("/topics/{topic_id}", response_model=TopicDetail)
def get_topic(topic_id: str, student_id: str | None = None, db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    topic = cur.topic(topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found")
    rows = student_svc.mastery_rows(db, student_id) if student_id else None
    return student_svc.topic_detail(cur, topic, rows)
