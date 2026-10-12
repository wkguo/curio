"""Misconception Classifier (spec §7) — picks the ONE gap to teach next."""

from harness.context import GradingKey, StudentSnapshot
from schemas.curriculum import Topic
from schemas.enums import MisconceptionType
from schemas.harness import CurriculumContext, Diagnosis, Mode, Verification
from services.llm import LLMClient, LLMError
from services.prompts import bullet, render, system_user

_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def classify_rules(v: Verification, key: GradingKey, snapshot: StudentSnapshot) -> Diagnosis:
    if v.misconceptions:
        m = sorted(v.misconceptions, key=lambda d: _SEVERITY_RANK[d.severity])[0]
        prev = snapshot.misconception_history.get(m.id or "", 0)
        return Diagnosis(
            type=m.type,
            misconception_id=m.id,
            label=m.label or m.statement,
            concept=m.concept,
            student_claim=m.student_claim,
            corrective_target=m.corrective_target,
            is_repeated=prev > 0,
            previous_occurrences=prev,
            classification="misconception",
            summary=f"{m.type.value.replace('_', ' ').title()}: {m.statement}" + (" (seen before)" if prev else ""),
        )
    missed_required = [p for p in key.required_points if p not in v.reasoning_points_hit]
    missing_text = "; ".join(key.point_text[p] for p in missed_required)
    if v.is_guess:
        return Diagnosis(
            type=MisconceptionType.GUESS_WITHOUT_REASONING,
            label="Guess without reasoning",
            concept=key.concept,
            corrective_target=missing_text or key.expected_answer,
            classification="guess",
            summary="No checkable reasoning yet — start from a simpler explanation.",
        )
    if v.classification == "unclear":
        return Diagnosis(
            concept=key.concept,
            classification="unclear",
            label="Not enough evidence",
            summary="Too vague to judge safely — ask the student to clarify before teaching.",
        )
    if v.reasoning_correct and v.answer_correct:
        return Diagnosis(concept=key.concept, classification="correct", summary="No gap found: answer and reasoning are both correct.")
    if v.answer_correct:
        t = MisconceptionType.CORRECT_BUT_INCOMPLETE if v.reasoning_points_hit else MisconceptionType.MISSING_STEP
        return Diagnosis(
            type=t,
            label="Missing reasoning step" if t == MisconceptionType.MISSING_STEP else "Correct but incomplete",
            concept=key.concept,
            corrective_target=missing_text,
            classification="incomplete",
            summary=f"Right answer, missing: {missing_text}",
        )
    if v.reasoning_points_hit:
        return Diagnosis(
            type=MisconceptionType.MISSING_STEP,
            label="Missing reasoning step",
            concept=key.concept,
            corrective_target=missing_text,
            classification="incomplete",
            summary=f"Partly on track, missing: {missing_text}",
        )
    return Diagnosis(
        type=MisconceptionType.FACTUAL_ERROR,
        label="Factual error",
        concept=key.concept,
        corrective_target=key.expected_answer,
        classification="incorrect",
        summary="The answer does not match the science yet.",
    )


async def classify_misconception(
    llm: LLMClient, v: Verification, key: GradingKey, ctx: CurriculumContext, snapshot: StudentSnapshot, topic: Topic
) -> tuple[Diagnosis, Mode]:
    rule_d = classify_rules(v, key, snapshot)
    # The LLM is only consulted for a *novel* misconception the curriculum doesn't name;
    # known ones are classified by the curated pack (cheaper, deterministic, auditable).
    novel = [m for m in v.misconceptions if not m.id]
    if not (llm.available and novel):
        return rule_d, "rules"
    try:
        prompt = render(
            "misconception_classifier",
            concept_name=ctx.concept_name,
            learning_objective=ctx.learning_objective,
            misconceptions=bullet([f"{m.id}: {m.statement}" for m in topic.misconceptions]),
            verification=v.model_dump_json(),
            previous=0,
        )
        d = await llm.generate(system_user(prompt), schema=Diagnosis)
        d.concept = d.concept if topic.concept(d.concept) else key.concept
        return d, "llm"
    except LLMError:
        return rule_d, "fallback"
