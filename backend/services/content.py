"""Concept pathways and their teacher-review status (proposal: every pathway should be
teacher-reviewed before the AI uses it; enforced when CURIO_REQUIRE_REVIEWED_CONTENT=true)."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from curriculum.loader import Curriculum
from models.tables import ContentReview
from schemas.api import MisconceptionCard, Pathway, PathwayTransfer
from services.students import NotFound


def _reviews(db: Session) -> dict[str, ContentReview]:
    return {r.pathway_id: r for r in db.scalars(select(ContentReview)).all()}


def pathways(db: Session, curriculum: Curriculum, topic_id: str | None = None) -> list[Pathway]:
    reviews = _reviews(db)
    out = []
    for t in curriculum.topics:
        if topic_id and t.topic_id != topic_id:
            continue
        for q in t.questions:
            c = t.concept(q.concept)
            r = reviews.get(q.id)
            out.append(
                Pathway(
                    id=q.id,
                    theme=t.theme,
                    topic_id=t.topic_id,
                    topic_name=t.name,
                    concept_id=c.id,
                    concept_name=c.name,
                    learning_objective=c.learning_objective,
                    diagnostic_question=q.prompt,
                    expected_explanation=q.expected_answer,
                    reasoning_points=[p.point for p in q.expected_reasoning],
                    required_points=[next(p.point for p in q.expected_reasoning if p.id == rid) for rid in q.required_points],
                    misconceptions=[
                        MisconceptionCard(id=m.id, label=m.label, statement=m.statement, corrective_target=m.corrective_target, concept=m.concept, type=m.type.value)
                        for m in (t.misconception(mid) for mid in q.misconceptions)
                        if m
                    ],
                    hints=q.hints,
                    transfer_questions=[
                        PathwayTransfer(id=tq.id, prompt=tq.prompt, expected_answer=tq.expected_answer, reasoning=[p.point for p in tq.expected_reasoning])
                        for tq in q.transfer_questions
                    ],
                    mastery_criterion=c.mastery_criterion,
                    review_status=r.status if r else "draft",
                    reviewer=r.reviewer if r else None,
                    review_note=r.note if r else "",
                    reviewed_at=r.updated_at if r else None,
                )
            )
    return out


def set_review(db: Session, curriculum: Curriculum, pathway_id: str, status: str, reviewer: str, note: str) -> Pathway:
    if not curriculum.question(pathway_id):
        raise NotFound(f"pathway {pathway_id} not found")
    r = db.get(ContentReview, pathway_id) or ContentReview(pathway_id=pathway_id)
    r.status, r.reviewer, r.note, r.updated_at = status, reviewer, note, datetime.now(timezone.utc)
    db.merge(r)
    db.commit()
    return next(p for p in pathways(db, curriculum) if p.id == pathway_id)


def approved_ids(db: Session) -> set[str]:
    return {r.pathway_id for r in _reviews(db).values() if r.status == "approved"}
