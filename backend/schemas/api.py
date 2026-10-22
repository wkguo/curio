"""Request/response models for the HTTP API (spec §18). Mirrored in frontend/types/api.ts."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from schemas.curriculum import Position
from schemas.enums import MasteryStatus
from schemas.harness import (
    AnalysisFeedback,
    Diagnosis,
    LearningState,
    MasteryChange,
    PublicQuestion,
    QuestionQuality,
    TeachingResponse,
    TraceStep,
    Verification,
)


# ----------------------------------------------------------------- curriculum
class TopicSummary(BaseModel):
    topic_id: str
    name: str
    subject: str
    level: str
    emoji: str
    color: str
    tagline: str
    description: str
    concept_count: int
    question_count: int
    mastery: float | None = None
    theme: str = ""
    syllabus_ref: str = ""


class ConceptNode(BaseModel):
    id: str
    topic_id: str
    name: str
    emoji: str
    summary: str
    learning_objective: str
    key_ideas: list[str]
    prerequisites: list[str]
    position: Position
    mastery: float = 0.0
    status: MasteryStatus = MasteryStatus.NEW
    attempts: int = 0
    verified: int = 0
    misconceptions: list[str] = Field(default_factory=list)
    mastery_criterion: str = ""


class GraphEdge(BaseModel):
    source: str
    target: str


class MisconceptionCard(BaseModel):
    id: str
    label: str
    statement: str
    corrective_target: str
    concept: str
    type: str


class TopicDetail(TopicSummary):
    concepts: list[ConceptNode]
    edges: list[GraphEdge]
    misconceptions: list[MisconceptionCard] = Field(default_factory=list)


# ----------------------------------------------------------------- students
class StudentProfile(BaseModel):
    id: str
    display_name: str
    level: str
    class_name: str
    avatar: str
    streak_days: int
    xp: int
    is_demo: bool


class TopicProgress(BaseModel):
    topic_id: str
    name: str
    emoji: str
    color: str
    mastery: float
    mastered: int
    learning: int
    total: int


class StudentMasteryResponse(BaseModel):
    student_id: str
    concept_mastery: dict[str, float]
    concepts: list[ConceptNode]
    topics: list[TopicProgress]


class ActivityItem(BaseModel):
    id: str
    kind: str
    topic_id: str
    concept_id: str
    concept_name: str
    question_prompt: str
    result: str  # verified | learning | needs_practice
    mastery_before: float | None
    mastery_after: float | None
    created_at: datetime


class HistoryPoint(BaseModel):
    date: str
    mastery: float
    answers: int = 0


class NextUp(BaseModel):
    topic_id: str
    concept_id: str
    concept_name: str
    reason: str


class TodayStats(BaseModel):
    questions_answered: int
    verified: int
    xp_today: int
    goal: int = 5


class DashboardResponse(BaseModel):
    student: StudentProfile
    topics: list[TopicProgress]
    current_topic: TopicProgress
    current_concepts: list[ConceptNode]
    today: TodayStats
    recent_activity: list[ActivityItem]
    next_up: NextUp | None
    insight: str
    history: list[HistoryPoint]
    badges: list[dict[str, Any]]


# ----------------------------------------------------------------- learning
class StartSessionRequest(BaseModel):
    student_id: str
    topic_id: str
    size: int = Field(default=5, ge=1, le=10)


class QuestionCard(BaseModel):
    id: str
    topic_id: str
    concept_id: str
    concept_name: str
    prompt: str
    emoji: str
    difficulty: int
    hints: list[str]
    demo_answers: dict[str, str] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    session_id: str
    topic_id: str
    topic_name: str
    topic_color: str
    questions: list[QuestionCard]
    current_index: int
    total: int


class SubmitRequest(BaseModel):
    student_id: str
    question_id: str
    answer: str = Field(max_length=1000)
    session_id: str | None = None


class SafetyNotice(BaseModel):
    """Student-facing result of the safety & privacy layer (never contains the redacted values)."""

    category: str
    message: str
    redactions: list[str] = Field(default_factory=list)


class SubmitResponse(BaseModel):
    """`blocked=True` means the safety layer stopped grading: only `safety` and `trace` are set."""

    interaction_id: str | None = None
    trace_id: str
    mode: str
    blocked: bool = False
    safety: SafetyNotice | None = None
    learning_state: LearningState | None = None
    verification: Verification | None = None
    diagnosis: Diagnosis | None = None
    feedback: AnalysisFeedback | None = None
    teaching_strategy: str | None = None
    strategy_reason: str = ""
    teaching_response: TeachingResponse | None = None
    transfer_question: PublicQuestion | None = None
    question_quality: QuestionQuality | None = None
    mastery_before: float | None = None
    mastery_after: float | None = None
    mastery_change: MasteryChange | None = None
    trace: list[TraceStep]
    transfer_demo_answer: str = ""


class ReplyRequest(BaseModel):
    student_id: str
    interaction_id: str
    message: str = Field(max_length=1000)


class ReplyResponse(BaseModel):
    interaction_id: str
    turn: int
    resolved: bool
    ready_for_transfer: bool
    deferred: bool = False
    blocked: bool = False
    safety: SafetyNotice | None = None
    learning_state: LearningState | None = None
    analysis: AnalysisFeedback | None = None
    teaching_response: TeachingResponse
    trace: list[TraceStep]


class TransferRequest(BaseModel):
    student_id: str
    interaction_id: str
    answer: str = Field(max_length=1000)


class TransferResponse(BaseModel):
    """`next_state`: mastered | verified | reteach | revisit. On `reteach`, Curio re-teaches
    (`teaching_response`) and asks a second question back (`next_transfer_question`)."""

    interaction_id: str
    trace_id: str
    blocked: bool = False
    safety: SafetyNotice | None = None
    learning_state: LearningState | None = None
    next_state: str = "verified"
    mastery_confirmed: bool = False
    mastery_before: float | None = None
    mastery_after: float | None = None
    mastery_change: MasteryChange | None = None
    concept_status: MasteryStatus | None = None
    feedback: str = ""
    verification: Verification | None = None
    teaching_response: TeachingResponse | None = None
    next_transfer_question: PublicQuestion | None = None
    next_transfer_demo_answer: str = ""
    attempt: int = 1
    xp_earned: int = 0
    trace: list[TraceStep]


class SafeError(BaseModel):
    """Spec §25 — the only error shape a student ever sees."""

    message: str = "Curio is having trouble checking that answer right now. Let's try this question another way."
    code: str = "curio_unavailable"


# ----------------------------------------------------------------- analytics
class MisconceptionStat(BaseModel):
    id: str
    label: str
    statement: str
    topic_id: str
    topic_name: str
    concept_id: str
    concept_name: str
    students: int
    occurrences: int
    resolved_rate: float


class TopicStat(BaseModel):
    topic_id: str
    name: str
    color: str
    emoji: str
    avg_mastery: float
    mastered: int
    learning: int
    needs_practice: int


class StrategyStat(BaseModel):
    strategy: str
    uses: int
    success_rate: float


class DayStat(BaseModel):
    date: str
    answers: int
    verified: int


class StudentRow(BaseModel):
    id: str
    display_name: str
    avatar: str
    avg_mastery: float
    answered: int
    verified: int
    top_misconception: str | None
    scores: dict[str, float]


class HeatmapConcept(BaseModel):
    id: str
    name: str
    topic_id: str


class ClassAnalytics(BaseModel):
    class_name: str
    students: int
    questions_answered: int
    verified_mastery_rate: float
    avg_mastery: float
    active_today: int
    answer_vs_reasoning: dict[str, int]
    top_misconceptions: list[MisconceptionStat]
    topics: list[TopicStat]
    strategies: list[StrategyStat]
    activity: list[DayStat]
    heatmap_concepts: list[HeatmapConcept]
    roster: list[StudentRow]
    classification_mix: dict[str, int] = Field(default_factory=dict)
    safety_events: dict[str, int] = Field(default_factory=dict)
    open_reviews: int = 0
    loop_outcomes: dict[str, int] = Field(default_factory=dict)


class DialogueTurn(BaseModel):
    role: str  # student | curio
    text: str
    strategy: str | None = None


class TraceSummary(BaseModel):
    id: str
    interaction_id: str
    student_id: str
    student_name: str
    avatar: str
    topic_id: str
    concept_id: str
    concept_name: str
    question_prompt: str
    answer: str
    answer_correct: bool | None
    reasoning_correct: bool | None
    misconception_label: str | None
    strategy: str | None
    mastery_before: float | None
    mastery_after: float | None
    transfer_confirmed: bool | None
    mode: str
    total_ms: int
    created_at: datetime


class TraceDetail(TraceSummary):
    verification: dict[str, Any]
    diagnosis: dict[str, Any]
    feedback: dict[str, Any]
    teaching: dict[str, Any]
    dialogue: list[DialogueTurn]
    transfer_question: dict[str, Any] | None
    transfer_answer: str | None
    transfer_feedback: str | None
    transfer_verification: dict[str, Any] | None
    final_mastery: float | None
    steps: list[TraceStep]
    transfer_steps: list[TraceStep]
    learning_state: dict[str, Any] | None = None
    transfer_attempts: list[dict[str, Any]] = Field(default_factory=list)


# ----------------------------------------------------------------- teacher review & content
class ReviewItem(BaseModel):
    id: str
    kind: str  # safety | deferred | persistent_misconception | stuck
    category: str
    severity: str
    student_id: str
    student_name: str
    avatar: str
    question_id: str | None
    question_prompt: str | None
    excerpt: str
    status: str
    note: str = ""
    created_at: datetime


class ResolveRequest(BaseModel):
    note: str = Field(default="", max_length=500)


class PathwayTransfer(BaseModel):
    id: str
    prompt: str
    expected_answer: str
    reasoning: list[str]


class Pathway(BaseModel):
    """One concept pathway (proposal): Theme → Topic → LO → Concept → Expected Explanation →
    Misconception → Diagnostic Question → Follow-up Question → Mastery Criterion."""

    id: str
    theme: str
    topic_id: str
    topic_name: str
    concept_id: str
    concept_name: str
    learning_objective: str
    diagnostic_question: str
    expected_explanation: str
    reasoning_points: list[str]
    required_points: list[str]
    misconceptions: list[MisconceptionCard]
    hints: list[str]
    transfer_questions: list[PathwayTransfer]
    mastery_criterion: str
    review_status: str  # draft | approved | flagged
    reviewer: str | None = None
    review_note: str = ""
    reviewed_at: datetime | None = None


class PathwayReviewRequest(BaseModel):
    status: str = Field(pattern="^(draft|approved|flagged)$")
    reviewer: str = Field(default="Teacher", max_length=64)
    note: str = Field(default="", max_length=500)


class PrivacySummary(BaseModel):
    student_id: str
    stored: dict[str, int]
    retention_days: int
    data_categories: list[str]
    not_collected: list[str]
