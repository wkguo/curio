"""Teaching Agent — turns (strategy, diagnosis) into short, age-appropriate chat bubbles.

Content priority (safety first for a children's product):
1. Teacher-authored block for this misconception + strategy (curated, reviewed).
2. LLM-generated block (when configured), validated against TeachingResponse.
3. Deterministic templates built from the curriculum pack.
"""

from harness.context import GradingKey, StudentSnapshot
from schemas.curriculum import Topic
from schemas.enums import MisconceptionType as M
from schemas.enums import TeachingStrategy as S
from schemas.harness import (
    AnalysisFeedback,
    CurriculumContext,
    Diagnosis,
    FeedbackConcern,
    Mode,
    ParsedProblem,
    StrategyDecision,
    TeachingResponse,
    Verification,
)
from harness.safety import check_output
from services.llm import LLMClient, LLMError
from services.prompts import bullet, render, system_user


# --------------------------------------------------------------------------- feedback
def build_feedback(
    v: Verification, d: Diagnosis, key: GradingKey, topic: Topic, snapshot: StudentSnapshot, parsed: ParsedProblem | None = None
) -> AnalysisFeedback:
    """The 'Curio is checking your reasoning...' panel (spec §4.2)."""
    strengths: list[str] = []
    if v.answer_correct:
        strengths.append(key.answer_praise)
    for pid in v.reasoning_points_hit:
        strengths.append(f"You explained that {key.point_text[pid][0].lower()}{key.point_text[pid][1:]}")

    concerns: list[FeedbackConcern] = []
    nudge = ""
    if d.needs_clarification:
        return AnalysisFeedback(
            headline="Tell me a bit more",
            strengths=["You had a go — that's how scientists start!"],
            nudge="I couldn't quite tell what you meant yet, so I'll ask before I explain anything.",
            tone="encourage",
        )
    if d.misconception_id and (m := topic.misconception(d.misconception_id)):
        concerns.append(FeedbackConcern(claim=d.student_claim or m.statement, note=m.nudge))
        nudge = m.nudge
    elif v.is_guess:
        nudge = "That's okay — let's build the idea together, one step at a time."
    elif d.has_gap:
        missing = [key.point_text[p] for p in key.required_points if p not in v.reasoning_points_hit]
        if missing:
            concerns.append(FeedbackConcern(claim="A step is missing from your explanation", note=key.hints[0] if key.hints else "Can you explain *why*?"))
        nudge = "Good start! A scientist would add one more step." if v.reasoning_points_hit else "Let's check the reason together: a scientist always explains *why*."
        if parsed is not None and not parsed.has_explanation:
            nudge = "You gave an answer — now tell me *why*. A “because …” makes it a scientist's answer."

    if not d.has_gap:
        headline, tone = f"Brilliant thinking, {snapshot.display_name}! 🌟", "celebrate"
        nudge = "Your answer AND your reasoning are both spot on. Let's see if you can use it somewhere new!"
    elif d.misconception_id:
        headline, tone = "One idea needs another look", "investigate"
    elif v.answer_correct and v.reasoning_points_hit:
        headline, tone = "Nice! Let's make your explanation complete", "encourage"
    elif v.answer_correct:
        headline, tone = "Let's check your reason together", "investigate"
    else:
        headline, tone = "Let's investigate together", "investigate"
    if parsed is not None and parsed.uncertain and d.has_gap:
        strengths.append("It's okay to feel unsure — let's check the idea together.")
    return AnalysisFeedback(headline=headline, strengths=strengths[:3], concerns=concerns, nudge=nudge, tone=tone)


# --------------------------------------------------------------------------- templates
def _template_response(decision: StrategyDecision, d: Diagnosis, key: GradingKey, ctx: CurriculumContext, topic: Topic, snapshot: StudentSnapshot) -> TeachingResponse:
    concept = topic.concept(ctx.concept_id)
    hint = key.hints[0] if key.hints else None
    missing = [key.point_text[p] for p in key.required_points]
    st = decision.strategy

    if st == S.CLARIFY:
        # Evidence is insufficient: do NOT teach content we can't verify — ask for more.
        focus = key.hints[0] if key.hints else "What do you think is happening, and what causes it?"
        return TeachingResponse(
            strategy=st,
            messages=[
                "Hmm, I want to make sure I understand your idea. 🤔",
                "Could you say a bit more? Try starting with **“I think … because …”**.",
            ],
            follow_up=focus,
            key_idea="",
        )
    if st == S.TRANSFER_EXAMPLE:
        return TeachingResponse(
            strategy=st,
            messages=[
                "You nailed both the answer **and** the reason. 🌟",
                "Real understanding means you can use an idea in a brand-new situation. Ready for a twist?",
            ],
            key_idea=concept.summary if concept else "",
            ready_for_transfer=True,
        )
    if st == S.PREREQUISITE_REVIEW:
        weak = [topic.concept(p) for p in ctx.prerequisites]
        weak = [w for w in weak if w and snapshot.mastery.get(w.id, 1.0) < 0.4] or [w for w in weak if w]
        pre = weak[0] if weak else concept
        return TeachingResponse(
            strategy=st,
            messages=[
                f"Let's warm up with an idea this question builds on: **{pre.name}**. 🧱",
                pre.summary,
                *(pre.key_ideas[:1]),
            ],
            follow_up=f"Using that idea, try again: {hint or key.prompt}",
            key_idea=pre.summary,
        )
    if st == S.SIMPLER_EXPLANATION:
        return TeachingResponse(
            strategy=st,
            messages=[
                "No worries — let's make it simpler. 🌱",
                concept.summary if concept else key.expected_answer,
            ],
            follow_up=hint or "Can you explain the question again in your own words, using that idea?",
            key_idea=concept.summary if concept else "",
        )
    if st in (S.SOCRATIC_QUESTION, S.DIRECT_HINT) and not d.misconception_id:
        if d.classification == "incorrect" or d.type == M.MISSING_STEP:
            msgs = ["Hmm, let's check the reason together. 🔍"]
        else:
            msgs = ["Good start! ✅ You're on the right track."]
        if st == S.DIRECT_HINT and missing:
            msgs.append(f"Here's a hint 💡 — think about this: {missing[0][0].lower()}{missing[0][1:]}")
        else:
            msgs.append("A scientist always explains *why*. Let's find the missing step together.")
        return TeachingResponse(
            strategy=st,
            messages=msgs,
            follow_up=hint or "Why does that happen? Try to explain the cause.",
            key_idea=d.corrective_target,
        )
    # Generic fallback for any other (strategy, misconception) pair.
    return TeachingResponse(
        strategy=st,
        messages=[
            "Let's look at this idea together. 🔍",
            concept.summary if concept else key.expected_answer,
        ],
        follow_up=hint or "What do you think happens now? Explain why.",
        key_idea=d.corrective_target or (concept.summary if concept else ""),
    )


def _authored_response(decision: StrategyDecision, d: Diagnosis, topic: Topic) -> TeachingResponse | None:
    if not d.misconception_id:
        return None
    m = topic.misconception(d.misconception_id)
    if not m:
        return None
    for strategy in [decision.strategy, *decision.alternatives]:
        block = m.teaching.get(strategy)
        if block:
            return TeachingResponse(
                strategy=strategy,
                messages=block.messages,
                follow_up=block.follow_up,
                visual=block.visual,
                key_idea=m.corrective_target,
            )
    return None


async def teach(
    llm: LLMClient,
    decision: StrategyDecision,
    d: Diagnosis,
    parsed: ParsedProblem,
    key: GradingKey,
    ctx: CurriculumContext,
    topic: Topic,
    snapshot: StudentSnapshot,
) -> tuple[TeachingResponse, Mode]:
    authored = _authored_response(decision, d, topic)
    if authored:
        return authored, "rules"
    if llm.available and d.has_gap and not d.needs_clarification:
        try:
            prompt = render(
                "teaching_agent",
                student_age=snapshot.age,
                level=snapshot.level,
                strategy=decision.strategy.value,
                student_claim=d.student_claim or parsed.student_answer,
                corrective_target=d.corrective_target,
                concept_name=ctx.concept_name,
                learning_objective=ctx.learning_objective,
                key_ideas=bullet(ctx.key_ideas),
                question=key.prompt,
                student_answer=parsed.student_answer,
            )
            r = await llm.generate(system_user(prompt), schema=TeachingResponse)
            r.strategy, r.ready_for_transfer, r.messages = decision.strategy, False, r.messages[:4]
            if check_output(" ".join([*r.messages, r.follow_up or ""])):
                raise LLMError("generated teaching failed the output safety guard")
            return r, "llm"
        except LLMError:
            return _template_response(decision, d, key, ctx, topic, snapshot), "fallback"
    return _template_response(decision, d, key, ctx, topic, snapshot), "rules"
