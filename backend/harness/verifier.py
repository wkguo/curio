"""Reasoning Verifier (spec §6) — judges the answer AND the reasoning separately.

Rule path: regex evidence from the curriculum key (deterministic; powers demo mode).
LLM path: structured Verification from the model, then reconciled with the rule
path so that a curated, known misconception is never silently dropped.
"""

import re

from harness.context import GradingKey, topic_misconceptions
from harness.text import _compile, claim_around, matches, matches_reasoning, negated
from schemas.curriculum import Topic
from schemas.enums import MisconceptionType
from schemas.harness import CurriculumContext, DetectedMisconception, Mode, ParsedProblem, ReferenceSolution, Verification
from services.llm import LLMClient, LLMError
from services.prompts import bullet, render, system_user


_STOP = set(
    "that this with from when what which there their they them then than have does into your about would could should because "
    "same feel feels more less very just also after before other some each will were been being much many".split()
)


def _content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in _STOP}


def is_on_topic(parsed: ParsedProblem, key: GradingKey) -> bool:
    """Does the answer engage with the question's science at all? Used to separate an
    on-topic wrong answer (teach) from an answer too vague to judge (ask to clarify)."""
    # Only words from the expected explanation count — merely restating the question's
    # nouns ("the ice does something to the juice") is not evidence of a scientific claim.
    vocab = _content_words(" ".join([key.expected_answer, *key.point_text.values()])) - _content_words(key.prompt)
    return parsed.word_count >= 3 and bool(_content_words(parsed.normalized_answer) & vocab)


def derive_classification(v: Verification, on_topic: bool) -> str:
    if v.is_guess:
        return "guess"
    if v.misconceptions:
        return "misconception"
    if v.answer_correct and v.reasoning_correct:
        return "correct"
    if v.answer_correct or v.reasoning_points_hit:
        return "incomplete"
    return "incorrect" if on_topic else "unclear"


def require_explanation(v: Verification, parsed: ParsedProblem) -> None:
    """A bare final answer ("same time") is not an explanation — never credit it as correct."""
    if v.classification == "correct" and not parsed.has_explanation and parsed.word_count < 6:
        v.reasoning_correct = False
        v.classification = "incomplete"
        v.quality = "partially_correct"
        v.reasoning_summary = "Right answer, but no explanation was given."


def verify_rules(parsed: ParsedProblem, key: GradingKey, topic: Topic) -> Verification:
    text = parsed.normalized_answer
    miscs = topic_misconceptions(topic, key.misconceptions)
    # A misconception match that the student denies ("wool doesn't make heat") is not a misconception.
    found = {m.id: [x for p in m.patterns for x in _compile(p).finditer(text) if not negated(text, x.start(), x.end())] for m in miscs}
    # Text that expresses a misconception can never also count as correct reasoning
    # ("it needs a force to keep moving" must not earn the "keeps moving" point).
    blocked = [x.span() for xs in found.values() for x in xs]
    hits = [p.id for p in key.reasoning if matches_reasoning(p.patterns, text, blocked)]
    missed = [p.id for p in key.reasoning if p.id not in hits]
    required_missed = [pid for pid in key.required_points if pid not in hits]

    detected: list[DetectedMisconception] = []
    for m in miscs:
        frag = found[m.id][0].group(0) if found[m.id] else None
        if frag:
            detected.append(
                DetectedMisconception(
                    id=m.id,
                    type=m.type,
                    statement=m.statement,
                    student_claim=claim_around(parsed.student_answer, frag),
                    concept=m.concept,
                    severity="high" if m.type in (MisconceptionType.CAUSAL_ERROR, MisconceptionType.CONCEPT_CONFUSION) else "medium",
                    corrective_target=m.corrective_target,
                    label=m.label,
                )
            )

    is_guess = parsed.is_blank_or_guess and not hits
    if key.answer_patterns:
        answer_correct = matches(key.answer_patterns, text) and not is_guess  # "dunno" is not the answer "no"
    else:
        answer_correct = not required_missed
    reasoning_correct = not required_missed and not detected and not is_guess

    if answer_correct and reasoning_correct:
        quality = "correct"
    elif answer_correct or hits:
        quality = "partially_correct"
    else:
        quality = "incorrect"

    concepts_detected = [key.concept] if hits else []
    missing_concepts = [key.concept] if required_missed else []

    if is_guess:
        summary = "The student did not give a reason we can check yet (looks like a guess)."
    elif detected:
        d = detected[0]
        lead = "correctly identified the answer but" if answer_correct else "did not reach the answer and"
        summary = f"The student {lead} holds a misconception: {d.statement.rstrip('.').lower()}."
    elif reasoning_correct:
        summary = "The student gave the right answer with complete, correct reasoning."
    elif answer_correct:
        gap = "; ".join(key.point_text[p] for p in required_missed)
        summary = f"Right answer, but the explanation is missing a key step: {gap}"
    else:
        summary = "The answer and reasoning do not yet match the expected explanation."

    confidence = 0.92 if detected else min(0.9, 0.7 + 0.08 * len(hits)) if hits else 0.65
    if parsed.uncertain:
        confidence -= 0.05
    v = Verification(
        answer_correct=answer_correct,
        reasoning_correct=reasoning_correct,
        confidence=round(confidence, 2),
        quality=quality,
        concepts_detected=concepts_detected,
        missing_concepts=missing_concepts,
        reasoning_points_hit=hits,
        reasoning_points_missed=missed,
        misconceptions=detected,
        is_guess=is_guess,
        reasoning_summary=summary,
    )
    v.classification = derive_classification(v, is_on_topic(parsed, key))
    require_explanation(v, parsed)
    if v.classification == "unclear":
        v.reasoning_summary = "The response is too vague to judge — Curio asks the student to clarify instead of teaching an unverified explanation."
        v.confidence = 0.4
    return v


def _reconcile(llm_v: Verification, rule_v: Verification, key: GradingKey, on_topic: bool) -> Verification:
    valid = [p.id for p in key.reasoning]
    llm_v.reasoning_points_hit = [p for p in valid if p in llm_v.reasoning_points_hit]
    llm_v.reasoning_points_missed = [p for p in valid if p not in llm_v.reasoning_points_hit]
    required_missed = [p for p in key.required_points if p not in llm_v.reasoning_points_hit]
    known = {m.id for m in llm_v.misconceptions if m.id}
    for m in rule_v.misconceptions:
        if m.id not in known:
            llm_v.misconceptions.append(m)
    if required_missed or llm_v.misconceptions or llm_v.is_guess:
        llm_v.reasoning_correct = False
        if required_missed:
            llm_v.reasoning_summary = "Reasoning not yet verified; missing evidence for: " + "; ".join(key.point_text[p] for p in required_missed)
        if llm_v.quality == "correct":
            llm_v.quality = "partially_correct" if llm_v.answer_correct or llm_v.reasoning_points_hit else "incorrect"
    llm_classification = llm_v.classification
    llm_v.classification = derive_classification(llm_v, on_topic)
    if llm_classification == "unclear" and llm_v.classification in ("incorrect", "incomplete") and not llm_v.reasoning_points_hit:
        llm_v.classification = "unclear"  # the model saw too little evidence — respect that
    return llm_v


async def verify_reasoning(
    llm: LLMClient,
    parsed: ParsedProblem,
    key: GradingKey,
    reference: ReferenceSolution,
    ctx: CurriculumContext,
    topic: Topic,
    student_age: int = 11,
) -> tuple[Verification, Mode]:
    rule_v = verify_rules(parsed, key, topic)
    if not llm.available:
        return rule_v, "rules"
    try:
        miscs = topic_misconceptions(topic, key.misconceptions)
        prompt = render(
            "reasoning_verifier",
            student_age=student_age,
            topic_name=ctx.topic_name,
            concept_name=ctx.concept_name,
            learning_objective=ctx.learning_objective,
            key_ideas=bullet(ctx.key_ideas),
            misconceptions=bullet([f"{m.id} ({m.type.value}): {m.statement}" for m in miscs]),
            expected_answer=reference.expected_answer,
            reasoning_points=bullet([f"{p.id}: {p.point}" for p in key.reasoning]),
            required_points=", ".join(key.required_points),
            question=key.prompt,
            student_answer=parsed.student_answer,
        )
        llm_v = await llm.generate(system_user(prompt), schema=Verification)
        llm_v = _reconcile(llm_v, rule_v, key, is_on_topic(parsed, key))
        require_explanation(llm_v, parsed)
        return llm_v, "llm"
    except LLMError:
        return rule_v, "fallback"
