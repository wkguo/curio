"""Transfer Question Generator (spec §9) with a bounded verify/regenerate loop (spec §10).

rules mode : pick the next teacher-authored transfer question the student hasn't seen.
LLM mode   : generate → verify → (regenerate once) → fall back to authored.
There is never more than one regeneration — no unbounded agent loops.
"""

import uuid

from harness.context import GradingKey, StudentSnapshot
from harness.question_verifier import verify_question
from schemas.curriculum import Question, Topic
from schemas.harness import CurriculumContext, Diagnosis, GeneratedQuestion, Mode, QuestionQuality
from harness.safety import check_output
from services.llm import LLMClient, LLMError
from services.prompts import bullet, render, system_user

EMOJI_HINT = "thermometer, spoon, cup, ice, soup, coat, magnet, soccer_ball, bicycle, apple, feather, droplet, cloud, balloon, teapot, bubbles, chair, pot, car, kite"


def pick_authored(question: Question, snapshot: StudentSnapshot) -> GeneratedQuestion | None:
    if not question.transfer_questions:
        return None
    unseen = [t for t in question.transfer_questions if t.id not in snapshot.seen_transfer_ids]
    tq = (unseen or question.transfer_questions)[0]
    return GeneratedQuestion(
        id=tq.id,
        concept=question.concept,
        prompt=tq.prompt,
        emoji=tq.emoji,
        expected_answer=tq.expected_answer,
        expected_reasoning=[p.point for p in tq.expected_reasoning],
        source="authored",
        authored_id=tq.id,
    )


def pick_next_transfer(question: Question, exclude: set[str]) -> GeneratedQuestion:
    """Second chance after a failed transfer: the next unseen authored transfer question,
    else a teach-back prompt graded against the original question's reasoning key."""
    for tq in question.transfer_questions:
        if tq.id not in exclude:
            return GeneratedQuestion(
                id=tq.id,
                concept=question.concept,
                prompt=tq.prompt,
                emoji=tq.emoji,
                expected_answer=tq.expected_answer,
                expected_reasoning=[p.point for p in tq.expected_reasoning],
                source="authored",
                authored_id=tq.id,
            )
    return GeneratedQuestion(
        id=f"{question.id}_teachback",
        concept=question.concept,
        prompt=f"Teach it back! Imagine your friend asks you this: “{question.prompt}” Explain the answer to them in your own words — what happens, and why?",
        emoji="speech_balloon",
        expected_answer=question.expected_answer,
        expected_reasoning=[p.point for p in question.expected_reasoning],
        source="teach_back",
    )


async def _generate_once(llm: LLMClient, question: Question, d: Diagnosis, ctx: CurriculumContext, snapshot: StudentSnapshot) -> GeneratedQuestion:
    prompt = render(
        "question_generator",
        student_age=snapshot.age,
        level=snapshot.level,
        concept_name=ctx.concept_name,
        concept_id=ctx.concept_id,
        learning_objective=ctx.learning_objective,
        key_ideas=bullet(ctx.key_ideas),
        question=question.prompt,
        corrective_target=d.corrective_target or question.expected_answer,
        emoji_keys=EMOJI_HINT,
    )
    g = await llm.generate(system_user(prompt), schema=GeneratedQuestion)
    g.id, g.source, g.concept, g.authored_id = f"gen_{uuid.uuid4().hex[:10]}", "generated", ctx.concept_id, None
    if check_output(g.prompt):
        raise LLMError("generated question failed the output safety guard")
    return g


async def generate_transfer_question(
    llm: LLMClient,
    question: Question,
    key: GradingKey,
    d: Diagnosis,
    ctx: CurriculumContext,
    topic: Topic,
    snapshot: StudentSnapshot,
) -> tuple[GeneratedQuestion, QuestionQuality, Mode, int]:
    """Returns (question, quality report, mode, attempts)."""
    authored = pick_authored(question, snapshot)
    if llm.available:
        for attempt in (1, 2):
            try:
                cand = await _generate_once(llm, question, d, ctx, snapshot)
            except LLMError:
                break
            quality, review_mode = await verify_question(llm, cand, key, ctx, topic)
            if review_mode == "fallback":
                break
            if quality.approved:
                return cand, quality, "llm", attempt
    if authored is None:  # a pack without authored transfer questions: reuse the concept summary
        c = topic.concept(ctx.concept_id)
        authored = GeneratedQuestion(
            id=f"{question.id}_fallback",
            concept=ctx.concept_id,
            prompt=f"In your own words, explain this idea with an example from home or school: {c.summary if c else question.expected_answer}",
            expected_answer=question.expected_answer,
            expected_reasoning=[p.point for p in question.expected_reasoning],
        )
    quality, _ = await verify_question(llm, authored, key, ctx, topic)
    return authored, quality, ("fallback" if llm.available else "rules"), 1
