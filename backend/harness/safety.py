"""Safety & privacy layer (proposal module 6; PDPC guidance on children's data).

Runs FIRST on every student message, before anything is stored or sent to a model:
* PII (phone, email, NRIC/FIN, address/postal code) is redacted — only the *kind* of
  redaction is recorded, never the value — and grading continues on the redacted text.
* Wellbeing concerns stop grading, show a supportive message with Singapore helplines,
  and raise a high-severity item in the teacher queue.
* Prompt-injection, off-topic chat and "just tell me the answer" requests stop grading
  and redirect the student back to the science question.

It also guards model OUTPUT (`check_output`) so generated text with personal data,
unsafe content or out-of-syllabus vocabulary is replaced by curated content.
"""

import re

from schemas.enums import SafetyCategory as C
from schemas.harness import SafetyReport

_PII = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("nric", re.compile(r"\b[STFGM]\d{7}[A-Z]\b", re.IGNORECASE)),
    ("phone", re.compile(r"(?:\+65[\s-]?)?\b[689]\d{3}[\s-]?\d{4}\b")),
    ("postal_code", re.compile(r"\b(?:singapore|s)\s*\(?\d{6}\)?", re.IGNORECASE)),
    ("address", re.compile(r"\b(?:i live (?:at|in)|my address is)\s+[\w#\-/ ]{0,40}\d+[\w#\-/]*", re.IGNORECASE)),
    ("address", re.compile(r"\b(?:blk|block)\s*\d+[a-z]?\b", re.IGNORECASE)),
]

_UNSAFE = re.compile(
    r"\b(kill (?:my ?self|me|him|her|them)|(?:want|wanna|wish i could) (?:to )?(?:die|disappear|not exist)|"
    r"hurt (?:my ?self|me|my \w+|him|her|them|someone|somebody)|hate myself|nobody (?:likes|loves|cares about) me|"
    r"suicide|cut myself|someone (?:is )?(?:hurting|hitting|touching) me|being bullied|abus(?:e|ing) me)\b",
    re.IGNORECASE,
)
_INJECTION = re.compile(
    r"(ignore (?:all |your |the )?(?:previous |above |prior )?(?:instructions|rules|prompt)|"
    r"system prompt|you are now|pretend (?:to be|you are)|act as (?:a|an|my)|developer mode|jailbreak|"
    r"reveal (?:your|the) (?:prompt|instructions))",
    re.IGNORECASE,
)
_ANSWER_REQUEST = re.compile(
    r"\b(?:tell|give|show|send) me the (?:correct |right |real )?(?:answer|ans)\b|"
    r"\bwhat(?:'?s| is) the (?:correct |right )?(?:answer|ans)\b|\bjust give (?:me )?(?:the )?(?:answer|ans)\b",
    re.IGNORECASE,
)
_OFF_TOPIC = re.compile(
    r"\b(roblox|minecraft|fortnite|youtube|tiktok|instagram|tell me a joke|what(?:'s| is) your name|"
    r"who are you|are you (?:a robot|real|human)|do my (?:math|maths|english|chinese|homework)|"
    r"write (?:me )?(?:an? )?(?:essay|story|poem)|play a game|i(?:'m| am) bored|your favou?rite|"
    r"world cup|who (?:do you think )?(?:will|would) win|k-?pop|anime|let'?s chat)\b",
    re.IGNORECASE,
)

HELPLINE = (
    "That sounds really important, and I'm glad you said something. 💜 "
    "Please talk to a trusted adult — a parent, your teacher or school counsellor — today. "
    "You can also call Tinkle Friend at 1800 2744 788 (free, for children). If you are in danger, call 999."
)


def redact(text: str) -> tuple[str, list[str]]:
    kinds: list[str] = []
    for kind, rx in _PII:
        text, n = rx.subn("[hidden]", text)
        if n:
            kinds.append(kind)
    return text, kinds


def screen_input(text: str, hint: str | None = None) -> SafetyReport:
    clean, kinds = redact(text)
    if _UNSAFE.search(text):
        return SafetyReport(
            category=C.UNSAFE, allow_grading=False, redacted_text=clean, redactions=kinds, notify_teacher=True, severity="high", student_message=HELPLINE
        )
    if _INJECTION.search(text):
        return SafetyReport(
            category=C.PROMPT_INJECTION,
            allow_grading=False,
            redacted_text=clean,
            redactions=kinds,
            notify_teacher=True,
            severity="low",
            student_message="Nice try! 😄 I can only help with this science question. What do you think the answer is — and why?",
        )
    if _ANSWER_REQUEST.search(text):
        msg = "I won't just hand you the answer — but I'll help you get there! 💪"
        if hint:
            msg += f" Here's a hint: {hint}"
        return SafetyReport(category=C.ANSWER_REQUEST, allow_grading=False, redacted_text=clean, redactions=kinds, severity="low", student_message=msg)
    if _OFF_TOPIC.search(text):
        return SafetyReport(
            category=C.OFF_TOPIC,
            allow_grading=False,
            redacted_text=clean,
            redactions=kinds,
            severity="low",
            student_message="That sounds fun, but I'm your science buddy! 🔬 Let's get back to the question — what do you think, and why?",
        )
    if kinds:
        return SafetyReport(
            category=C.PII,
            allow_grading=True,
            redacted_text=clean,
            redactions=kinds,
            notify_teacher=False,
            severity="medium",
            student_message="🔒 Quick tip: you don't need to share personal details (like phone numbers or addresses) with Curio. I've hidden them for you.",
        )
    return SafetyReport(redacted_text=clean)


# Words beyond the P5–P6 syllabus that generated teaching text must not introduce.
_OUT_OF_SCOPE = re.compile(
    r"\b(molecule|molecular|atom|atomic|kinetic|joule|thermodynamic|entropy|specific heat|coefficient|"
    r"newton'?s? (?:first|second|third)|momentum|electron|photon|quantum)\b",
    re.IGNORECASE,
)


def check_output(text: str) -> list[str]:
    """Return problems with model-generated text (empty list = safe to show)."""
    problems = []
    if redact(text)[1]:
        problems.append("contains personal data")
    if _UNSAFE.search(text):
        problems.append("unsafe content")
    if _OUT_OF_SCOPE.search(text):
        problems.append("out-of-syllabus vocabulary")
    return problems
