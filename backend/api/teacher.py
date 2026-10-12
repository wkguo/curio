"""Teacher-facing endpoints: review queue (safety / deferred / persistent misconceptions)
and concept-pathway content review. No auth in the MVP — demo users only (spec §24)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import curriculum_dep
from curriculum.loader import Curriculum
from database.session import get_db
from schemas.api import Pathway, PathwayReviewRequest, ResolveRequest, ReviewItem
from services import content, review
from services.students import NotFound

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


@router.get("/queue", response_model=list[ReviewItem])
def queue(status: str | None = "open", db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    return review.list_items(db, cur, status if status != "all" else None)


@router.post("/queue/{item_id}/resolve")
def resolve(item_id: str, req: ResolveRequest, db: Session = Depends(get_db)):
    try:
        review.resolve(db, item_id, req.note)
    except NotFound:
        raise HTTPException(404, "Review item not found")
    return {"ok": True}


@router.get("/pathways", response_model=list[Pathway])
def pathways(topic_id: str | None = None, db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    return content.pathways(db, cur, topic_id)


@router.post("/pathways/{pathway_id}/review", response_model=Pathway)
def review_pathway(pathway_id: str, req: PathwayReviewRequest, db: Session = Depends(get_db), cur: Curriculum = Depends(curriculum_dep)):
    try:
        return content.set_review(db, cur, pathway_id, req.status, req.reviewer, req.note)
    except NotFound:
        raise HTTPException(404, "Pathway not found")
