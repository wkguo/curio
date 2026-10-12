"""Inputs shared by the harness modules."""

from dataclasses import dataclass, field

from schemas.curriculum import Question, ReasoningPoint, Topic, TransferQuestion
from schemas.harness import GeneratedQuestion


@dataclass
class StudentSnapshot:
    """The slice of student state the harness is allowed to see (no PII beyond a first name)."""

    student_id: str
    display_name: str = "there"
    level: str = "Primary 5"
    age: int = 11
    mastery: dict[str, float] = field(default_factory=dict)
    misconception_history: dict[str, int] = field(default_factory=dict)
    last_strategy_for: dict[str, str] = field(default_factory=dict)
    seen_transfer_ids: set[str] = field(default_factory=set)


@dataclass
class GradingKey:
    """Uniform grading key for core, authored-transfer and generated questions."""

    question_id: str
    concept: str
    related_concepts: list[str]
    prompt: str
    answer_patterns: list[str]
    expected_answer: str
    reasoning: list[ReasoningPoint]
    required_points: list[str]
    misconceptions: list[str]
    hints: list[str]
    answer_praise: str = "You picked the right answer."

    @property
    def point_text(self) -> dict[str, str]:
        return {p.id: p.point for p in self.reasoning}

    @classmethod
    def from_question(cls, q: Question, candidate_misconceptions: list[str]) -> "GradingKey":
        return cls(
            question_id=q.id,
            concept=q.concept,
            related_concepts=q.related_concepts,
            prompt=q.prompt,
            answer_patterns=q.answer_patterns,
            expected_answer=q.expected_answer,
            reasoning=q.expected_reasoning,
            required_points=q.required_points,
            misconceptions=candidate_misconceptions,
            hints=q.hints,
            answer_praise=q.answer_praise,
        )

    @classmethod
    def from_transfer(cls, parent: Question, tq: TransferQuestion, candidate_misconceptions: list[str]) -> "GradingKey":
        return cls(
            question_id=tq.id,
            concept=parent.concept,
            related_concepts=parent.related_concepts,
            prompt=tq.prompt,
            answer_patterns=tq.answer_patterns,
            expected_answer=tq.expected_answer,
            reasoning=tq.expected_reasoning,
            required_points=tq.required_points,
            misconceptions=candidate_misconceptions,
            hints=[],
            answer_praise="You picked the right answer.",
        )

    @classmethod
    def from_generated(cls, parent: Question, gq: GeneratedQuestion, candidate_misconceptions: list[str]) -> "GradingKey":
        """Generated questions carry point *text*; the rule path borrows regexes from
        the parent's authored transfer key, which tests the same concept."""
        borrowed = parent.transfer_questions[0] if parent.transfer_questions else None
        reasoning = borrowed.expected_reasoning if borrowed else parent.expected_reasoning
        required = borrowed.required_points if borrowed else parent.required_points
        points = [
            ReasoningPoint(id=r.id, point=gq.expected_reasoning[i] if i < len(gq.expected_reasoning) else r.point, patterns=r.patterns)
            for i, r in enumerate(reasoning)
        ]
        return cls(
            question_id=gq.id,
            concept=gq.concept,
            related_concepts=parent.related_concepts,
            prompt=gq.prompt,
            answer_patterns=[],  # free-form generated answers: judged on reasoning
            expected_answer=gq.expected_answer,
            reasoning=points,
            required_points=required,
            misconceptions=candidate_misconceptions,
            hints=[],
        )


def topic_misconceptions(topic: Topic, ids: list[str]):
    return [m for m in (topic.misconception(i) for i in ids) if m is not None]
