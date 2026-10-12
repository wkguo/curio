"""Reference Solver — produces the answer key the verifier grades against.

Authored questions carry a teacher-written key, which is authoritative and costs
nothing. The LLM path is only used when a key is missing (e.g. a question that
arrives without one); its output is then validated like any other structured step.
"""

from harness.context import GradingKey
from schemas.harness import CurriculumContext, Mode, ReferenceSolution
from services.llm import LLMClient, LLMError
from services.prompts import bullet, render, system_user


async def solve_reference(llm: LLMClient, key: GradingKey, ctx: CurriculumContext) -> tuple[ReferenceSolution, Mode]:
    if key.reasoning:
        return (
            ReferenceSolution(
                expected_answer=key.expected_answer,
                reasoning_steps=[f"{p.id}: {p.point}" for p in key.reasoning],
                required_step_ids=key.required_points,
            ),
            "rules",
        )
    if llm.available:
        try:
            prompt = render(
                "reference_solver",
                topic_name=ctx.topic_name,
                concept_name=ctx.concept_name,
                learning_objective=ctx.learning_objective,
                key_ideas=bullet(ctx.key_ideas),
                question=key.prompt,
            )
            return await llm.generate(system_user(prompt), schema=ReferenceSolution), "llm"
        except LLMError:
            pass
    return ReferenceSolution(expected_answer=key.expected_answer, reasoning_steps=ctx.key_ideas, required_step_ids=[]), "fallback"
