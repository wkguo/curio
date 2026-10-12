"""Structured outputs of each pedagogical harness step (spec §5–§11, §22).

These models are the contract between harness modules, the LLM (they double as
JSON output schemas) and the API. Keep them flat and explicit.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.enums import LearningPhase, MisconceptionType, SafetyCategory, TeachingStrategy

Mode = Literal["llm", "rules", "fallback"]


class ParsedProblem(BaseModel):
    question_id: str
    topic_id: str
    concept_id: str
    student_answer: str
    normalized_answer: str
    word_count: int
    is_blank_or_guess: bool
    # Proposal module 1 — student-response analyser
    answer_part: str = ""
    explanation_part: str = ""
    has_explanation: bool = False
    uncertainty_markers: list[str] = Field(default_factory=list)

    @property
    def uncertain(self) -> bool:
        return bool(self.uncertainty_markers)


Classification = Literal["correct", "incomplete", "misconception", "incorrect", "unclear", "guess", "blocked"]


class SafetyReport(BaseModel):
    """Proposal module 6 — safety/privacy layer verdict for one student message."""

    category: SafetyCategory = SafetyCategory.NONE
    allow_grading: bool = True
    redacted_text: str
    redactions: list[str] = Field(default_factory=list)  # kinds only (e.g. "phone"), never the values
    notify_teacher: bool = False
    severity: Literal["none", "low", "medium", "high"] = "none"
    student_message: str = ""


class CurriculumContext(BaseModel):
    topic_id: str
    topic_name: str
    concept_id: str
    concept_name: str
    learning_objective: str
    key_ideas: list[str]
    prerequisites: list[str]
    related_concepts: list[str]
    candidate_misconceptions: list[str]


class ReferenceSolution(BaseModel):
    expected_answer: str
    reasoning_steps: list[str]
    required_step_ids: list[str]


class DetectedMisconception(BaseModel):
    id: str | None = None
    type: MisconceptionType
    statement: str
    student_claim: str = ""
    concept: str
    severity: Literal["low", "medium", "high"] = "medium"
    corrective_target: str = ""
    label: str = ""


class Verification(BaseModel):
    """Spec §6 — the structured reasoning verification."""

    answer_correct: bool
    reasoning_correct: bool
    confidence: float = Field(ge=0, le=1)
    quality: Literal["correct", "partially_correct", "incorrect"]
    concepts_detected: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    reasoning_points_hit: list[str] = Field(default_factory=list)
    reasoning_points_missed: list[str] = Field(default_factory=list)
    misconceptions: list[DetectedMisconception] = Field(default_factory=list)
    is_guess: bool = False
    classification: Classification = "incorrect"
    reasoning_summary: str


class Diagnosis(BaseModel):
    """Spec §7 — the primary learning gap the teacher should address."""

    type: MisconceptionType | None = None
    misconception_id: str | None = None
    label: str = ""
    concept: str
    student_claim: str = ""
    corrective_target: str = ""
    is_repeated: bool = False
    previous_occurrences: int = 0
    classification: Classification = "incorrect"
    summary: str

    @property
    def has_gap(self) -> bool:
        """True when Curio must act before the transfer question (teach or clarify)."""
        return self.type is not None or self.classification == "unclear"

    @property
    def needs_clarification(self) -> bool:
        return self.classification == "unclear"


class StrategyDecision(BaseModel):
    strategy: TeachingStrategy
    reason: str
    alternatives: list[TeachingStrategy] = Field(default_factory=list)


class FeedbackConcern(BaseModel):
    claim: str
    note: str


class AnalysisFeedback(BaseModel):
    """What the student sees in the 'Curio is checking your reasoning' panel."""

    headline: str
    strengths: list[str] = Field(default_factory=list)
    concerns: list[FeedbackConcern] = Field(default_factory=list)
    nudge: str = ""
    tone: Literal["celebrate", "encourage", "investigate"] = "investigate"


class TeachingResponse(BaseModel):
    strategy: TeachingStrategy
    messages: list[str]
    follow_up: str | None = None
    visual: str | None = None
    key_idea: str = ""
    ready_for_transfer: bool = False


class GeneratedQuestion(BaseModel):
    """A transfer question plus its grading key. Never sent to the client whole."""

    id: str
    concept: str
    prompt: str
    emoji: str = "light_bulb"
    expected_answer: str
    expected_reasoning: list[str]
    source: Literal["authored", "generated", "teach_back"] = "authored"
    authored_id: str | None = None


class PublicQuestion(BaseModel):
    id: str
    concept: str
    prompt: str
    emoji: str = "light_bulb"
    source: Literal["authored", "generated", "teach_back"] = "authored"


class QuestionQuality(BaseModel):
    """Spec §10."""

    same_concept: bool
    age_appropriate: bool
    answerable: bool
    curriculum_aligned: bool
    not_a_repeat: bool = True
    difficulty: Literal["easier", "similar", "harder"] = "similar"
    approved: bool
    notes: list[str] = Field(default_factory=list)


class MasteryChange(BaseModel):
    concept_id: str
    concept_name: str = ""
    before: float
    after: float
    evidence: float
    reason: str


class TraceStep(BaseModel):
    """Spec §22 — one step of the harness, rendered as a pipeline node."""

    key: str
    step: str
    status: Literal["complete", "skipped", "fallback", "error"] = "complete"
    mode: Mode = "rules"
    duration_ms: float = 0
    summary: str = ""
    output: dict[str, Any] = Field(default_factory=dict)


class StateTransition(BaseModel):
    from_phase: LearningPhase
    to_phase: LearningPhase
    trigger: str
    at: str


class LearningState(BaseModel):
    """Compact learning state (proposal: current concept, detected misconception,
    intervention used, mastery status) — recorded instead of relying on chat history."""

    concept_id: str
    concept_name: str
    phase: LearningPhase = LearningPhase.ATTEMPT
    classification: Classification | None = None
    misconception_id: str | None = None
    misconception_label: str | None = None
    intervention: TeachingStrategy | None = None
    mastery: float = 0.0
    mastery_status: str = "learning"
    transfer_attempts: int = 0
    deferred_reason: str | None = None
    history: list[StateTransition] = Field(default_factory=list)
