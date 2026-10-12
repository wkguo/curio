"""Small text utilities shared by the rule-based harness paths."""

import re
from functools import lru_cache

_GUESS = re.compile(
    r"^\s*(i\s*)?(don'?t|do not|dont)\s+know|^\s*(idk|dunno|no idea|not sure|no clue|guess|random|\?+|pass|skip)\b",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


@lru_cache(maxsize=4096)
def _compile(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


def first_match(patterns: list[str], text: str) -> str | None:
    """Return the matched substring of the first pattern that matches, else None."""
    for p in patterns:
        m = _compile(p).search(text)
        if m:
            return m.group(0)
    return None


def spans(patterns: list[str], text: str) -> list[tuple[int, int]]:
    return [m.span() for p in patterns for m in _compile(p).finditer(text)]


def matches_outside(patterns: list[str], text: str, blocked: list[tuple[int, int]]) -> bool:
    """True if some match of `patterns` does not overlap any blocked span."""
    return any(all(e <= bs or s >= be for bs, be in blocked) for s, e in spans(patterns, text))


def matches(patterns: list[str], text: str) -> bool:
    return first_match(patterns, text) is not None


def word_count(text: str) -> int:
    return len(re.findall(r"[a-zA-Z0-9']+", text))


def looks_like_guess(text: str, answer_patterns: list[str] | None = None) -> bool:
    """Explicit don't-know, empty, or a lone word that isn't even a candidate answer.
    A short real answer ("the bathtub") is NOT a guess — it's an answer without reasoning."""
    if _GUESS.search(text) or not re.search(r"[a-z]", text):
        return True
    return word_count(text) <= 1 and not (answer_patterns and matches(answer_patterns, text))


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def jaccard(a: str, b: str) -> float:
    ta = set(re.findall(r"[a-z]{3,}", a.lower()))
    tb = set(re.findall(r"[a-z]{3,}", b.lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def claim_around(text: str, fragment: str, max_len: int = 90) -> str:
    """Return the sentence of `text` containing `fragment` — used to quote the student's claim."""
    for s in sentences(text):
        if fragment.lower() in s.lower():
            return s.strip()[:max_len]
    return fragment[:max_len]
