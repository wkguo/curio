"""Question Quality Verifier (spec §10) — lightweight gate before a child sees a
generated transfer question. Rule checks always run; the LLM reviewer adds a
second opinion for generated questions when available."""

import re

from harness.context import GradingKey
from harness.text import jaccard, sentences, word_count
from schemas.curriculum import Topic
from schemas.harness import CurriculumContext, GeneratedQuestion, Mode, QuestionQuality
from services.llm import LLMClient, LLMError
from services.prompts import render, system_user

# Vocabulary beyond the Singapore primary syllabus; a transfer question must not need it.
OUT_OF_SCOPE = re.compile(
    r"\b(molecule|molecular|atom|kinetic|joule|newton'?s? (first|second|third)|thermodynamic|entropy|specific heat|coefficient|acceleration|momentum|electron|photon)\b",
    re.IGNORECASE,
)
UNSAFE = re.compile(r"\b(knife|blood|kill|die|death|weapon|alcohol|beer|wine|cigarette|gun|fire alarm prank)\b", re.IGNORECASE)


def check_rules(candidate: GeneratedQuestion, original: GradingKey, ctx: CurriculumContext, topic: Topic) -> QuestionQuality:
    notes: list[str] = []
    same_concept = candidate.concept == ctx.concept_id
    if not same_concept:
        notes.append(f"concept {candidate.concept} ≠ {ctx.concept_id}")
    sents = sentences(candidate.prompt) or [candidate.prompt]
    avg_len = word_count(candidate.prompt) / max(1, len(sents))
    age_ok = avg_len <= 24 and word_count(candidate.prompt) <= 70 and not OUT_OF_SCOPE.search(candidate.prompt)
    if not age_ok:
        notes.append(f"readability: {avg_len:.0f} words/sentence or out-of-scope vocabulary")
    safe = not UNSAFE.search(candidate.prompt)
    if not safe:
        notes.append("contains content unsuitable for children")
    answerable = bool(candidate.expected_answer.strip()) and len(candidate.expected_reasoning) >= 1 and "?" in candidate.prompt
    if not answerable:
        notes.append("no clear expected answer or no question mark")
    aligned = topic.concept(candidate.concept) is not None
    overlap = jaccard(candidate.prompt, original.prompt)
    not_repeat = overlap < 0.55
    if not not_repeat:
        notes.append(f"too similar to the original (overlap {overlap:.2f})")
    approved = all([same_concept, age_ok, safe, answerable, aligned, not_repeat])
    return QuestionQuality(
        same_concept=same_concept,
        age_appropriate=age_ok and safe,
        answerable=answerable,
        curriculum_aligned=aligned,
        not_a_repeat=not_repeat,
        difficulty="similar",
        approved=approved,
        notes=notes or ["all checks passed"],
    )


async def verify_question(
    llm: LLMClient, candidate: GeneratedQuestion, original: GradingKey, ctx: CurriculumContext, topic: Topic
) -> tuple[QuestionQuality, Mode]:
    q = check_rules(candidate, original, ctx, topic)
    if not (q.approved and llm.available and candidate.source == "generated"):
        return q, "rules"
    try:
        prompt = render(
            "question_verifier",
            concept_name=ctx.concept_name,
            learning_objective=ctx.learning_objective,
            question=original.prompt,
            candidate=candidate.model_dump_json(include={"prompt", "expected_answer", "expected_reasoning"}),
        )
        judged = await llm.generate(system_user(prompt), schema=QuestionQuality)
        judged.approved = all([
            judged.approved, q.approved, judged.same_concept, judged.age_appropriate,
            judged.answerable, judged.curriculum_aligned, judged.not_a_repeat, judged.difficulty != "harder",
        ])
        judged.notes = [*q.notes, *judged.notes][:6]
        return judged, "llm"
    except LLMError:
        q.approved = False
        q.notes.append("model review unavailable; use an authored question")
        return q, "fallback"
