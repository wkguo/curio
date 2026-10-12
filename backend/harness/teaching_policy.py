"""Teaching Policy (spec §8) — a transparent heuristic, deliberately pure.

The function signature (diagnosis, student state) -> StrategyDecision is the seam
where a learned policy (bandit / RL) can later be dropped in.
"""

from harness.context import StudentSnapshot
from schemas.enums import MisconceptionType as M
from schemas.enums import TeachingStrategy as S
from schemas.harness import CurriculumContext, Diagnosis, StrategyDecision

BASE_POLICY: dict[M, S] = {
    M.FACTUAL_ERROR: S.DIRECT_HINT,
    M.CAUSAL_ERROR: S.COUNTEREXAMPLE,
    M.CONCEPT_CONFUSION: S.ANALOGY,
    M.MISSING_STEP: S.SOCRATIC_QUESTION,
    M.CORRECT_BUT_INCOMPLETE: S.SOCRATIC_QUESTION,
    M.OVERGENERALIZATION: S.COUNTEREXAMPLE,
    M.VOCABULARY_CONFUSION: S.ANALOGY,
    M.GUESS_WITHOUT_REASONING: S.SIMPLER_EXPLANATION,
}

# When the first choice has already been tried on this student, rotate through these.
ROTATION: list[S] = [S.VISUAL_EXPLANATION, S.ANALOGY, S.COUNTEREXAMPLE, S.SOCRATIC_QUESTION, S.DIRECT_HINT, S.SIMPLER_EXPLANATION]

PREREQ_THRESHOLD = 0.4


def select_strategy(diagnosis: Diagnosis, snapshot: StudentSnapshot, ctx: CurriculumContext) -> StrategyDecision:
    if diagnosis.needs_clarification:
        return StrategyDecision(
            strategy=S.CLARIFY,
            reason="Evidence is insufficient to judge — ask the student to clarify instead of teaching an unverified explanation.",
            alternatives=[],
        )

    if not diagnosis.has_gap:
        return StrategyDecision(
            strategy=S.TRANSFER_EXAMPLE,
            reason="Reasoning verified — confirm understanding with a transfer question.",
            alternatives=[],
        )

    weak_prereqs = [p for p in ctx.prerequisites if snapshot.mastery.get(p, 1.0) < PREREQ_THRESHOLD]
    base = BASE_POLICY.get(diagnosis.type, S.SIMPLER_EXPLANATION)
    alternatives = [s for s in ROTATION if s != base]

    if weak_prereqs:
        return StrategyDecision(
            strategy=S.PREREQUISITE_REVIEW,
            reason=f"Prerequisite mastery is low ({', '.join(weak_prereqs)} < {PREREQ_THRESHOLD:.0%}); review it first.",
            alternatives=[base, *alternatives],
        )

    if diagnosis.is_repeated and diagnosis.misconception_id:
        tried = snapshot.last_strategy_for.get(diagnosis.misconception_id)
        choice = next(s for s in [base, *ROTATION] if s.value != tried)
        return StrategyDecision(
            strategy=choice,
            reason=f"Misconception seen {diagnosis.previous_occurrences}× before"
            + (f" and {tried.replace('_', ' ').lower()} was already tried" if tried else "")
            + " — switch approach.",
            alternatives=[s for s in [base, *ROTATION] if s != choice],
        )

    return StrategyDecision(
        strategy=base,
        reason=f"{diagnosis.type.value.replace('_', ' ').title()} → {base.value.replace('_', ' ').title()} (base policy).",
        alternatives=alternatives,
    )
