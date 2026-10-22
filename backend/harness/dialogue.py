"""Teaching dialogue turn (spec §20): after the first teaching message the student
replies; Curio checks whether the targeted idea has been repaired.

Bounded: at most MAX_TURNS replies, then Curio states the key idea and moves on to
the transfer question — the student is never stuck in a loop.
"""

from dataclasses import dataclass

from harness.context import GradingKey
from harness.text import is_dont_know, matches, normalize
from schemas.curriculum import Topic
from schemas.enums import TeachingStrategy
from schemas.harness import TeachingResponse

MAX_TURNS = 2


@dataclass
class DialogueOutcome:
    resolved: bool
    misconception_reappeared: bool
    response: TeachingResponse
    dont_know: bool = False


def evaluate_reply(
    reply: str,
    turn: int,
    key: GradingKey,
    topic: Topic,
    misconception_id: str | None,
    strategy_used: str,
    missing_points: list[str],
) -> DialogueOutcome:
    text = normalize(reply)
    m = topic.misconception(misconception_id) if misconception_id else None
    reappeared = bool(m and matches(m.patterns, text))

    hit_missing = [pid for pid in missing_points if matches(next(p.patterns for p in key.reasoning if p.id == pid), text)]
    resolved = not reappeared and (
        (m is not None and matches(m.resolution_patterns, text)) or (bool(missing_points) and len(hit_missing) == len(missing_points))
    )
    if m is None and not missing_points:
        resolved = not reappeared

    if resolved:
        confirm = m.confirm if (m and m.confirm) else [f"Exactly! 🎉 {key.point_text[missing_points[0]]}" if missing_points else "Exactly! 🎉"]
        return DialogueOutcome(
            True,
            False,
            TeachingResponse(
                strategy=TeachingStrategy(strategy_used),
                messages=[*confirm, "Now let's check you can use this idea somewhere new. 🚀"],
                key_idea=m.corrective_target if m else key.expected_answer,
                ready_for_transfer=True,
            ),
        )

    # "I don't know" is honest, not wrong: never answer it with "getting closer".
    dont_know = not reappeared and is_dont_know(text)  # `text` is already normalized

    if turn >= MAX_TURNS:
        idea = m.corrective_target if m else key.expected_answer
        return DialogueOutcome(
            False,
            reappeared,
            TeachingResponse(
                strategy=TeachingStrategy.DIRECT_HINT,
                messages=[
                    "That's okay — not knowing yet is where learning starts. 🌱" if dont_know else "Thanks for thinking so hard about this! 💪",
                    f"Here's the key idea: **{idea}**",
                    "Let's try using it on a new example.",
                ],
                key_idea=idea,
                ready_for_transfer=True,
            ),
            dont_know,
        )

    # Try a different angle: next authored strategy for the misconception, else a hint.
    if m:
        for strategy, block in m.teaching.items():
            if strategy.value != strategy_used:
                if dont_know:
                    lead = "That's okay! Let's look at it another way. 🌱"
                elif reappeared:
                    lead = "I can see why it feels that way! Let's test it differently. 🤔"
                else:
                    lead = "Hmm, not quite yet — let's try another way. 🤔"
                return DialogueOutcome(
                    False,
                    reappeared,
                    TeachingResponse(
                        strategy=strategy,
                        messages=[lead, *block.messages],
                        follow_up=block.follow_up,
                        visual=block.visual,
                        key_idea=m.corrective_target,
                    ),
                    dont_know,
                )
    hint = key.hints[min(turn, len(key.hints) - 1)] if key.hints else None
    target = key.point_text[missing_points[0]] if missing_points else key.expected_answer
    return DialogueOutcome(
        False,
        reappeared,
        TeachingResponse(
            strategy=TeachingStrategy.DIRECT_HINT,
            messages=[
                "That's okay — let's take a smaller step. 🌱" if dont_know else "Getting closer! 🔍",
                f"Hint 💡 — {hint}" if hint else "Think about what causes it.",
            ],
            follow_up=f"Can you explain it using this idea: “{target[0].lower()}{target[1:]}”?" if turn >= 1 else "What do you think now?",
            key_idea=target,
        ),
        dont_know,
    )
