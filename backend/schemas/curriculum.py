"""Pydantic schema for curriculum packs (curriculum/data/*.yaml).

Validation here is the mechanical guard for curriculum authors: every regex must
compile and every cross-reference must resolve, otherwise the app refuses to start
and the error names the file, the id and the broken field.
"""

import re

from pydantic import BaseModel, Field, field_validator, model_validator

from schemas.enums import MisconceptionType, TeachingStrategy


def _check_patterns(patterns: list[str]) -> list[str]:
    for p in patterns:
        try:
            re.compile(p, re.IGNORECASE)
        except re.error as exc:  # pragma: no cover - exercised by tests via bad data
            raise ValueError(f"invalid regex {p!r}: {exc}") from exc
    return patterns


class Position(BaseModel):
    x: float = 0
    y: float = 0


class ReasoningPoint(BaseModel):
    id: str
    point: str
    patterns: list[str] = Field(default_factory=list)

    _v = field_validator("patterns")(classmethod(lambda cls, v: _check_patterns(v)))


class TeachingBlock(BaseModel):
    messages: list[str]
    follow_up: str | None = None
    visual: str | None = None


class Concept(BaseModel):
    id: str
    name: str
    emoji: str = "light_bulb"
    learning_objective: str
    summary: str
    prerequisites: list[str] = Field(default_factory=list)
    key_ideas: list[str] = Field(default_factory=list)
    mastery_criterion: str = ""
    position: Position = Field(default_factory=Position)

    @model_validator(mode="after")
    def _default_criterion(self):
        if not self.mastery_criterion:
            self.mastery_criterion = f"Explains, in a new situation, that {self.learning_objective[0].lower()}{self.learning_objective[1:]}"
        return self


class Misconception(BaseModel):
    id: str
    label: str = ""
    nudge: str = "Let's investigate this idea together."
    concept: str
    type: MisconceptionType
    statement: str
    corrective_target: str
    patterns: list[str]
    resolution_patterns: list[str] = Field(default_factory=list)
    teaching: dict[TeachingStrategy, TeachingBlock] = Field(default_factory=dict)
    confirm: list[str] = Field(default_factory=list)

    _v1 = field_validator("patterns")(classmethod(lambda cls, v: _check_patterns(v)))
    _v2 = field_validator("resolution_patterns")(classmethod(lambda cls, v: _check_patterns(v)))

    @model_validator(mode="after")
    def _default_label(self):
        if not self.label:
            self.label = self.statement.rstrip(".")[:40]
        return self


class TransferQuestion(BaseModel):
    id: str
    prompt: str
    emoji: str = "light_bulb"
    answer_patterns: list[str] = Field(default_factory=list)
    expected_answer: str
    expected_reasoning: list[ReasoningPoint]
    required_points: list[str]
    demo_answer: str = ""

    _v = field_validator("answer_patterns")(classmethod(lambda cls, v: _check_patterns(v)))

    @model_validator(mode="after")
    def _required_exist(self):
        ids = {p.id for p in self.expected_reasoning}
        missing = set(self.required_points) - ids
        if missing:
            raise ValueError(f"transfer question {self.id}: required_points {missing} not in expected_reasoning")
        return self


class DemoAnswers(BaseModel):
    misconception: str = ""
    dialogue: str = ""
    correct: str = ""


class Question(BaseModel):
    id: str
    concept: str
    related_concepts: list[str] = Field(default_factory=list)
    difficulty: int = Field(default=2, ge=1, le=5)
    emoji: str = "light_bulb"
    prompt: str
    answer_praise: str = "You picked the right answer."
    answer_patterns: list[str] = Field(default_factory=list)
    expected_answer: str
    expected_reasoning: list[ReasoningPoint]
    required_points: list[str]
    misconceptions: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    demo_answers: DemoAnswers = Field(default_factory=DemoAnswers)
    transfer_questions: list[TransferQuestion] = Field(default_factory=list)

    _v = field_validator("answer_patterns")(classmethod(lambda cls, v: _check_patterns(v)))

    @model_validator(mode="after")
    def _required_exist(self):
        ids = {p.id for p in self.expected_reasoning}
        missing = set(self.required_points) - ids
        if missing:
            raise ValueError(f"question {self.id}: required_points {missing} not in expected_reasoning")
        return self


class Topic(BaseModel):
    topic_id: str
    name: str
    subject: str = "Primary Science"
    level: str = "Primary 5–6"
    theme: str = ""
    syllabus_ref: str = ""
    emoji: str = "light_bulb"
    color: str = "#7C5CFF"
    tagline: str = ""
    description: str = ""
    concepts: list[Concept]
    misconceptions: list[Misconception] = Field(default_factory=list)
    questions: list[Question]

    @model_validator(mode="after")
    def _references(self):
        concept_ids = {c.id for c in self.concepts}
        misc_ids = {m.id for m in self.misconceptions}
        errors: list[str] = []
        for c in self.concepts:
            for p in c.prerequisites:
                if p not in concept_ids:
                    errors.append(f"concept {c.id}: unknown prerequisite {p}")
        for m in self.misconceptions:
            if m.concept not in concept_ids:
                errors.append(f"misconception {m.id}: unknown concept {m.concept}")
        for q in self.questions:
            for cid in [q.concept, *q.related_concepts]:
                if cid not in concept_ids:
                    errors.append(f"question {q.id}: unknown concept {cid}")
            for mid in q.misconceptions:
                if mid not in misc_ids:
                    errors.append(f"question {q.id}: unknown misconception {mid}")
        if errors:
            raise ValueError(f"topic {self.topic_id}: " + "; ".join(errors))
        return self

    # -- lookups ---------------------------------------------------------
    def concept(self, concept_id: str) -> Concept | None:
        return next((c for c in self.concepts if c.id == concept_id), None)

    def misconception(self, misconception_id: str) -> Misconception | None:
        return next((m for m in self.misconceptions if m.id == misconception_id), None)

    def question(self, question_id: str) -> Question | None:
        return next((q for q in self.questions if q.id == question_id), None)
