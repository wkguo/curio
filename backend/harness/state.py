"""Learning-state machine (proposal: explicit state transition after each attempt).

    attempt ─┬─ blocked                      (safety layer)
             ├─ clarifying ─┬─ teaching / transfer
             │              └─ deferred      (still unclear → teacher review)
             ├─ teaching ── transfer
             └─ transfer ─┬─ mastered | verified
                          └─ reteach ── transfer ─┬─ mastered | verified
                                                  └─ revisit (+ teacher flag if the misconception persists)

Mastery is only ever granted from the transfer phase (evidence-based gating).
"""

from datetime import datetime, timezone

from harness.mastery import MASTERED_AT
from schemas.enums import LearningPhase as P
from schemas.harness import Diagnosis, LearningState, StateTransition

MAX_TRANSFER_ATTEMPTS = 2

ALLOWED: dict[P, set[P]] = {
    P.ATTEMPT: {P.BLOCKED, P.CLARIFYING, P.TEACHING, P.TRANSFER},
    P.BLOCKED: {P.ATTEMPT},
    P.CLARIFYING: {P.CLARIFYING, P.TEACHING, P.TRANSFER, P.DEFERRED},
    P.TEACHING: {P.TEACHING, P.TRANSFER},
    P.TRANSFER: {P.MASTERED, P.VERIFIED, P.RETEACH, P.REVISIT},
    P.RETEACH: {P.TRANSFER},
    P.MASTERED: set(),
    P.VERIFIED: set(),
    P.REVISIT: set(),
    P.DEFERRED: set(),
}


class InvalidTransition(ValueError):
    pass


def new_state(concept_id: str, concept_name: str, mastery: float) -> LearningState:
    return LearningState(concept_id=concept_id, concept_name=concept_name, mastery=mastery)


def transition(state: LearningState, to: P, trigger: str) -> LearningState:
    if to not in ALLOWED[state.phase]:
        raise InvalidTransition(f"{state.phase.value} → {to.value} is not a valid learning-state transition")
    state.history.append(StateTransition(from_phase=state.phase, to_phase=to, trigger=trigger, at=datetime.now(timezone.utc).isoformat()))
    state.phase = to
    return state


def phase_after_diagnosis(d: Diagnosis) -> P:
    if d.needs_clarification:
        return P.CLARIFYING
    return P.TEACHING if d.has_gap else P.TRANSFER


def phase_after_transfer(confirmed: bool, mastery_after: float, attempts: int) -> P:
    if confirmed:
        return P.MASTERED if mastery_after >= MASTERED_AT else P.VERIFIED
    return P.RETEACH if attempts < MAX_TRANSFER_ATTEMPTS else P.REVISIT


def apply_diagnosis(state: LearningState, d: Diagnosis, intervention) -> LearningState:
    state.classification = d.classification
    state.misconception_id = d.misconception_id
    state.misconception_label = d.label or None
    state.intervention = intervention
    return state
