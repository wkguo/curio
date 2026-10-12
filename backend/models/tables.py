"""SQLAlchemy tables (spec §23).

students, concepts, questions, student_mastery, learning_sessions,
student_responses, agent_traces — plus `mastery_events` so the progress page can
chart mastery over time.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(64))
    level: Mapped[str] = mapped_column(String(32), default="Primary 5")
    class_name: Mapped[str] = mapped_column(String(32), default="5 Curiosity")
    avatar: Mapped[str] = mapped_column(String(32), default="fox")
    is_demo: Mapped[bool] = mapped_column(default=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    mastery: Mapped[list["StudentMastery"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class ConceptRow(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    topic_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128))
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)


class QuestionRow(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    topic_id: Mapped[str] = mapped_column(String(64), index=True)
    concept_id: Mapped[str] = mapped_column(String(64), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(16), default="core")  # core | transfer | generated
    payload: Mapped[dict] = mapped_column(JSON, default=dict)  # grading key for generated questions


class StudentMastery(Base):
    __tablename__ = "student_mastery"
    __table_args__ = (UniqueConstraint("student_id", "concept_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[str] = mapped_column(String(64), index=True)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    verified_count: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    student: Mapped[Student] = relationship(back_populates="mastery")


class MasteryEvent(Base):
    __tablename__ = "mastery_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[str] = mapped_column(String(64), index=True)
    before: Mapped[float] = mapped_column(Float)
    after: Mapped[float] = mapped_column(Float)
    evidence: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[str] = mapped_column(String(64))
    question_ids: Mapped[list] = mapped_column(JSON, default=list)
    current_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | completed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StudentResponse(Base):
    __tablename__ = "student_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("learning_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("student_responses.id", ondelete="CASCADE"), nullable=True, index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[str] = mapped_column(String(64), index=True)
    question_id: Mapped[str] = mapped_column(String(64), index=True)
    concept_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # initial | dialogue | transfer
    answer: Mapped[str] = mapped_column(Text)
    answer_correct: Mapped[bool | None] = mapped_column(nullable=True)
    reasoning_correct: Mapped[bool | None] = mapped_column(nullable=True)
    misconception_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    misconception_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    strategy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    transfer_question_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dialogue_turns: Mapped[int] = mapped_column(Integer, default=0)
    resolved: Mapped[bool] = mapped_column(default=False)
    mastery_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    mastery_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)  # verification / diagnosis / teaching / feedback
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    response_id: Mapped[str] = mapped_column(ForeignKey("student_responses.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(16))
    mode: Mapped[str] = mapped_column(String(16), default="rules")
    steps: Mapped[list] = mapped_column(JSON, default=list)
    total_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ReviewQueueItem(Base):
    """Cases the AI must not handle alone: wellbeing/safety flags, unclear answers deferred
    after clarification, and misconceptions that persist through re-teaching."""

    __tablename__ = "review_queue"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(16), default="low")
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    response_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    question_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, default="")  # already PII-redacted
    status: Mapped[str] = mapped_column(String(16), default="open")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ContentReview(Base):
    """Teacher review status of a concept pathway (proposal: teacher-reviewed before AI use)."""

    __tablename__ = "content_reviews"

    pathway_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    reviewer: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Meta(Base):
    __tablename__ = "meta"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))
