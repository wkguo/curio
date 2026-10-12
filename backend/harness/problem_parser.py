"""Student-response analyser (proposal module 1).

Separates the final answer from the stated explanation and records uncertainty
markers, so a correct final answer is never mistaken for a full explanation.
"""

import re

from harness.context import GradingKey
from harness.text import looks_like_guess, normalize, word_count
from schemas.harness import ParsedProblem

MAX_ANSWER_CHARS = 600

_BECAUSE = re.compile(r"\b(because|cos|cuz|since|so that|so|as|due to|therefore|that'?s why|which means|this means)\b", re.IGNORECASE)
_UNCERTAIN = re.compile(r"\b(maybe|i think|i guess|not sure|perhaps|probably|might|i'?m not sure|possibly)\b", re.IGNORECASE)


def parse_problem(key: GradingKey, topic_id: str, student_answer: str) -> ParsedProblem:
    answer = (student_answer or "").strip()[:MAX_ANSWER_CHARS]
    norm = normalize(answer)
    m = _BECAUSE.search(norm)
    answer_part, explanation_part = (norm[: m.start()].strip(" ,.;"), norm[m.end() :].strip()) if m else (norm, "")
    return ParsedProblem(
        question_id=key.question_id,
        topic_id=topic_id,
        concept_id=key.concept,
        student_answer=answer,
        normalized_answer=norm,
        word_count=word_count(norm),
        is_blank_or_guess=looks_like_guess(norm, getattr(key, "answer_patterns", None)),
        answer_part=answer_part,
        explanation_part=explanation_part,
        has_explanation=bool(m and word_count(explanation_part) >= 2),
        uncertainty_markers=sorted({u.lower() for u in _UNCERTAIN.findall(norm)}),
    )
