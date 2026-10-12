from enum import Enum


class MisconceptionType(str, Enum):
    FACTUAL_ERROR = "FACTUAL_ERROR"
    CAUSAL_ERROR = "CAUSAL_ERROR"
    CONCEPT_CONFUSION = "CONCEPT_CONFUSION"
    MISSING_STEP = "MISSING_STEP"
    OVERGENERALIZATION = "OVERGENERALIZATION"
    VOCABULARY_CONFUSION = "VOCABULARY_CONFUSION"
    CORRECT_BUT_INCOMPLETE = "CORRECT_BUT_INCOMPLETE"
    GUESS_WITHOUT_REASONING = "GUESS_WITHOUT_REASONING"


class TeachingStrategy(str, Enum):
    DIRECT_HINT = "DIRECT_HINT"
    SOCRATIC_QUESTION = "SOCRATIC_QUESTION"
    ANALOGY = "ANALOGY"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    SIMPLER_EXPLANATION = "SIMPLER_EXPLANATION"
    PREREQUISITE_REVIEW = "PREREQUISITE_REVIEW"
    VISUAL_EXPLANATION = "VISUAL_EXPLANATION"
    TRANSFER_EXAMPLE = "TRANSFER_EXAMPLE"
    # Proposal: when evidence is insufficient, ask for clarification instead of teaching
    # an unverified explanation.
    CLARIFY = "CLARIFY"


class MasteryStatus(str, Enum):
    MASTERED = "mastered"
    LEARNING = "learning"
    NEEDS_PRACTICE = "needs_practice"
    NEW = "new"
    LOCKED = "locked"


class InteractionKind(str, Enum):
    INITIAL = "initial"
    DIALOGUE = "dialogue"
    TRANSFER = "transfer"


class LearningPhase(str, Enum):
    """Explicit learning-state machine (proposal: 'explicit state transition after each attempt')."""

    ATTEMPT = "attempt"
    BLOCKED = "blocked"  # safety layer stopped grading
    CLARIFYING = "clarifying"  # evidence insufficient → ask the student to say more
    TEACHING = "teaching"  # gap diagnosed → targeted teaching dialogue
    TRANSFER = "transfer"  # question back in a new context
    RETEACH = "reteach"  # transfer failed → re-enter teaching with a second transfer question
    MASTERED = "mastered"  # transfer verified and mastery threshold reached
    VERIFIED = "verified"  # transfer verified, mastery still growing
    REVISIT = "revisit"  # two transfer attempts failed → schedule for later
    DEFERRED = "deferred"  # cannot judge safely → teacher review


class SafetyCategory(str, Enum):
    NONE = "none"
    PII = "pii"
    UNSAFE = "unsafe"
    PROMPT_INJECTION = "prompt_injection"
    OFF_TOPIC = "off_topic"
    ANSWER_REQUEST = "answer_request"


# Response classification (proposal module 3: correct / incomplete / misconception-linked, plus
# the evidence-insufficient and safety outcomes the loop must handle explicitly).
CLASSIFICATIONS = ("correct", "incomplete", "misconception", "incorrect", "unclear", "guess", "blocked")
