"""Mastery Estimator (spec §11): mastery_new = clamp(mastery_old + lr * evidence).

Evidence table (spec §11):
  1.0  correct reasoning + transfer success
  0.5  correct reasoning
  0.2  partial understanding (right answer OR some reasoning points)
  0.0  guess / no evidence
 -0.1  repeated misconception
"""

from schemas.enums import MasteryStatus
from schemas.harness import Diagnosis, Verification

MASTERED_AT = 0.75
LEARNING_AT = 0.45
LOCK_BELOW = 0.45


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def initial_evidence(v: Verification, d: Diagnosis) -> tuple[float, str]:
    if v.classification == "unclear":
        return 0.0, "not enough evidence yet — clarification requested"
    if v.is_guess:
        return 0.0, "guess — no evidence of understanding"
    if d.is_repeated:
        return -0.1, f"repeated misconception: {d.label}"
    if v.answer_correct and v.reasoning_correct:
        return 0.5, "correct answer + correct reasoning"
    if v.answer_correct or v.reasoning_points_hit:
        if v.answer_correct and not v.reasoning_correct:
            return 0.2, "correct answer but reasoning not yet verified"
        return 0.2, "partial understanding"
    return 0.0, "incorrect — no evidence yet"


def transfer_evidence(v: Verification, repeated: bool) -> tuple[float, str]:
    if v.answer_correct and v.reasoning_correct:
        return 1.0, "transfer success — understanding verified in a new context"
    if repeated:
        return -0.1, "misconception reappeared on transfer"
    if v.misconceptions:
        return 0.0, f"misconception on transfer: {v.misconceptions[0].label or v.misconceptions[0].statement}"
    if v.answer_correct or v.reasoning_points_hit:
        return 0.2, "partial transfer"
    return 0.0, "transfer not yet successful"


def update(before: float, evidence: float, learning_rate: float) -> float:
    return round(clamp(before + learning_rate * evidence), 4)


def status_for(score: float, attempts: int, prereq_scores: list[float], verified: int = 1) -> MasteryStatus:
    """Evidence-based mastery gating (proposal): a high score alone is not mastery —
    the student must also have passed at least one transfer question."""
    if score >= MASTERED_AT and verified >= 1:
        return MasteryStatus.MASTERED
    if attempts == 0 and score == 0 and any(p < LOCK_BELOW for p in prereq_scores):
        return MasteryStatus.LOCKED
    if score >= LEARNING_AT:
        return MasteryStatus.LEARNING
    if attempts == 0 and score == 0:
        return MasteryStatus.NEW
    return MasteryStatus.NEEDS_PRACTICE
