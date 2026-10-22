"""Small text utilities shared by the rule-based harness paths."""

import re
from functools import lru_cache

_GUESS_WORDS = re.compile(r"\b(?:guess|random|pass|skip)\b")
_GUESS = re.compile(
    r"^\s*(i\s*)?(don'?t|do not|dont)\s+know|^\s*(idk|dunno|no idea|not sure|no clue|guess|random|\?+|pass|skip)\b",
    re.IGNORECASE,
)


_CONTRACTIONS = re.compile(r"\b(do|does|did|is|are|was|were|can|could|should|would|won|have|has|had)nt\b", re.IGNORECASE)


def normalize(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = _CONTRACTIONS.sub(lambda m: f"{m.group(1)}n't", text)  # "dont need to touch" == "don't need to touch"
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


# Only explicit denials: "wool doesn't make heat", "not because the sun melts it". A bare "no" is the
# answer ("No, because the sugar melted") and "cannot"/"never" often carry the misconception itself.
_DENIAL = re.compile(r"(?:doesn't|don't|didn't|isn't|aren't|\b(?:does|do|is|are) not|\bnot because|\bnot true that)\s+(?:[a-z']+\s+){0,3}$")


_DENIAL_INSIDE = re.compile(r"doesn't|don't|didn't|isn't|aren't|\b(?:does|do|is|are) not\b")


def negated(text: str, start: int, end: int | None = None) -> bool:
    """Is the span [start, end) denied by an explicit negation just before it or inside it?"""
    return bool(_DENIAL.search(text[:start])) or (end is not None and bool(_DENIAL_INSIDE.search(text[start:end])))


def matches(patterns: list[str], text: str) -> bool:
    return first_match(patterns, text) is not None


def word_count(text: str) -> int:
    return len(re.findall(r"[a-zA-Z0-9']+", text))


def looks_like_guess(text: str, answer_patterns: list[str] | None = None) -> bool:
    """Explicit don't-know, empty, or a lone word that isn't even a candidate answer.
    A short real answer ("the bathtub") is NOT a guess — it's an answer without reasoning."""
    if _GUESS.search(text) or not re.search(r"[a-z]", text) or is_dont_know(text):
        return True
    return word_count(text) <= 1 and not (answer_patterns and matches(answer_patterns, text))


_DONT_KNOW = re.compile(
    r"\b(?:don'?t|do not|dont)\s+(?:know|no|get|understand)\b|\bdunno\b|\bidk\b|\bno (?:idea|clue)\b|\bnot sure\b|\bgive up\b|\bstill confused\b|\bhuh\b"
)
# Words that may surround a don't-know without being an attempt ("hmm i still dont get it lah").
_FILLER = set(
    "i im i'm really still just lah lor leh sia sorry um umm hmm hm oh ok okay sir miss teacher the it this that to what so haha ha have a an but yeah yes "
    "answer question one why how is no not".split()
)


def has_non_english_script(text: str) -> bool:
    """Chinese / Tamil / Japanese / Korean letters: Curio only grades English answers."""
    return bool(re.search(r"[\u0b80-\u0bff\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", text))


def is_dont_know(text: str) -> bool:
    """"I don't know" / "idk" / "still dont get it" / "???" with no attempt to reason.
    "not sure, metal is colder" is an attempt: anything left after the phrase must be filler."""
    if has_non_english_script(text):
        return False
    if not re.search(r"[a-z]", text):
        return True
    t = _DONT_KNOW.sub(" ", _GUESS_WORDS.sub(" ", text))
    if t == text:
        return False
    rest = [w for w in re.findall(r"[a-z']+", t) if w not in _FILLER]
    return not rest and word_count(text) <= 10


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
