"""Privacy controls (PDPC Advisory Guidelines on children's personal data, 2024):
data minimisation, a visible inventory of what is stored, deletion and retention."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from config import get_settings
from models.tables import AgentTrace, LearningSession, MasteryEvent, ReviewQueueItem, StudentMastery, StudentResponse
from schemas.api import PrivacySummary

DATA_CATEGORIES = [
    "First name or nickname and an avatar picture (no surname)",
    "Level and class label",
    "Your answers to science questions (personal details are hidden automatically before saving)",
    "Mastery scores per science concept",
    "How Curio decided what to teach (structured steps, not raw AI prompts)",
]
NOT_COLLECTED = [
    "Full name, NRIC/FIN, birthday, address, phone number or email",
    "Photos, voice or location",
    "Chat outside the science question (Curio redirects off-topic messages)",
]


def summary(db: Session, student_id: str) -> PrivacySummary:
    def count(model):
        return db.scalar(select(func.count()).select_from(model).where(model.student_id == student_id)) or 0

    return PrivacySummary(
        student_id=student_id,
        stored={
            "answers_and_dialogue": count(StudentResponse),
            "mastery_records": count(StudentMastery),
            "mastery_history_events": count(MasteryEvent),
            "decision_traces": count(AgentTrace),
            "learning_sessions": count(LearningSession),
        },
        retention_days=get_settings().retention_days,
        data_categories=DATA_CATEGORIES,
        not_collected=NOT_COLLECTED,
    )


def delete_learning_data(db: Session, student_id: str) -> dict[str, int]:
    out = {}
    for name, model in [
        ("traces", AgentTrace),
        ("review_items", ReviewQueueItem),
        ("responses", StudentResponse),
        ("mastery_events", MasteryEvent),
        ("sessions", LearningSession),
        ("mastery", StudentMastery),
    ]:
        out[name] = db.execute(delete(model).where(model.student_id == student_id)).rowcount or 0
    db.commit()
    return out


def purge_expired(db: Session) -> dict[str, int]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=get_settings().retention_days)
    out = {}
    for name, model in [("traces", AgentTrace), ("responses", StudentResponse), ("mastery_events", MasteryEvent), ("review_items", ReviewQueueItem)]:
        out[name] = db.execute(delete(model).where(model.created_at < cutoff)).rowcount or 0
    db.commit()
    return out
