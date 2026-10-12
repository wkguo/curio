"""Teacher review queue: safety flags, deferred (unjudgeable) answers, persistent misconceptions."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from curriculum.loader import Curriculum
from models.tables import ReviewQueueItem, Student
from schemas.api import ReviewItem
from services.students import NotFound

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "none": 3}


def add_item(
    db: Session, *, kind: str, category: str, severity: str, student_id: str, excerpt: str, question_id: str | None = None, response_id: str | None = None, when=None
) -> ReviewQueueItem:
    item = ReviewQueueItem(
        id=str(uuid.uuid4()),
        kind=kind,
        category=category,
        severity=severity,
        student_id=student_id,
        response_id=response_id,
        question_id=question_id,
        excerpt=excerpt[:300],
    )
    if when is not None:
        item.created_at = when
    db.add(item)
    return item


def list_items(db: Session, curriculum: Curriculum, status: str | None = "open") -> list[ReviewItem]:
    stmt = select(ReviewQueueItem).order_by(ReviewQueueItem.created_at.desc())
    if status:
        stmt = stmt.where(ReviewQueueItem.status == status)
    out = []
    for it in db.scalars(stmt).all():
        s = db.get(Student, it.student_id)
        pair = curriculum.question(it.question_id) if it.question_id else None
        out.append(
            ReviewItem(
                id=it.id,
                kind=it.kind,
                category=it.category,
                severity=it.severity,
                student_id=it.student_id,
                student_name=s.display_name if s else it.student_id,
                avatar=s.avatar if s else "fox",
                question_id=it.question_id,
                question_prompt=pair[1].prompt if pair else None,
                excerpt=it.excerpt,
                status=it.status,
                note=it.note,
                created_at=it.created_at,
            )
        )
    out.sort(key=lambda r: SEVERITY_ORDER.get(r.severity, 9))
    return out


def resolve(db: Session, item_id: str, note: str) -> None:
    it = db.get(ReviewQueueItem, item_id)
    if not it:
        raise NotFound(f"review item {item_id} not found")
    it.status, it.note = "resolved", note
    db.commit()
