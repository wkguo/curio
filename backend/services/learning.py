"""Learning flow service: sessions, submit → reply → transfer, persistence of traces."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from curriculum.loader import Curriculum
from harness import mastery as mastery_model
from harness.dialogue import MAX_TURNS
from harness.text import is_dont_know, normalize
from config import get_settings
from harness import state as sm
from harness.orchestrator import BlockedResult, PedagogicalHarness, Tracer
from models.tables import AgentTrace, LearningSession, QuestionRow, StudentResponse
from schemas.api import (
    QuestionCard,
    SafetyNotice,
    ReplyResponse,
    SessionResponse,
    SubmitResponse,
    TransferResponse,
)
from schemas.enums import LearningPhase as P
from schemas.harness import GeneratedQuestion, LearningState, PublicQuestion, SafetyReport, TeachingResponse
from services import content as content_svc
from services import review as review_svc
from services import students as student_svc
from services.students import NotFound

XP_ANSWER, XP_REASONING, XP_TRANSFER = 10, 15, 25


class ContentNotReviewed(RuntimeError):
    """Raised when CURIO_REQUIRE_REVIEWED_CONTENT is on and a topic has no approved pathway."""


def _uid() -> str:
    return str(uuid.uuid4())


def question_card(curriculum: Curriculum, question_id: str, *, include_demo: bool) -> QuestionCard:
    pair = curriculum.question(question_id)
    if not pair:
        raise NotFound(f"question {question_id} not found")
    topic, q = pair
    c = topic.concept(q.concept)
    demo = {}
    if include_demo:
        demo = {k: v for k, v in q.demo_answers.model_dump().items() if v}
    return QuestionCard(
        id=q.id,
        topic_id=topic.topic_id,
        concept_id=q.concept,
        concept_name=c.name if c else q.concept,
        prompt=q.prompt,
        emoji=q.emoji,
        difficulty=q.difficulty,
        hints=q.hints,
        demo_answers=demo,
    )


def start_session(db: Session, curriculum: Curriculum, student_id: str, topic_id: str, size: int) -> SessionResponse:
    student = student_svc.get_student(db, student_id)
    topic = curriculum.topic(topic_id)
    if not topic:
        raise NotFound(f"topic {topic_id} not found")
    rows = student_svc.mastery_rows(db, student_id)
    # Demo student: authored order, so the scripted demo (heat_001 first) is deterministic.
    # Others: weakest concepts first.
    qs = list(topic.questions)
    if get_settings().require_reviewed_content:
        approved = content_svc.approved_ids(db)
        qs = [q for q in qs if q.id in approved]
        if not qs:
            raise ContentNotReviewed(f"No teacher-approved pathways in {topic.name} yet.")
    if not student.is_demo:
        qs.sort(key=lambda q: rows[q.concept].mastery_score if q.concept in rows else 0.0)
    qs = qs[:size]
    sess = LearningSession(id=_uid(), student_id=student_id, topic_id=topic_id, question_ids=[q.id for q in qs])
    db.add(sess)
    db.commit()
    return SessionResponse(
        session_id=sess.id,
        topic_id=topic_id,
        topic_name=topic.name,
        topic_color=topic.color,
        questions=[question_card(curriculum, q.id, include_demo=student.is_demo) for q in qs],
        current_index=0,
        total=len(qs),
    )


def _save_trace(db: Session, response: StudentResponse, tr: Tracer, when: datetime | None = None) -> AgentTrace:
    t = AgentTrace(
        id=_uid(),
        response_id=response.id,
        student_id=response.student_id,
        question_id=response.question_id,
        kind=response.kind,
        mode=tr.mode,
        steps=[s.model_dump(mode="json") for s in tr.steps],
        total_ms=tr.total_ms,
        created_at=when or datetime.now(timezone.utc),
    )
    db.add(t)
    return t



def _notice(r: SafetyReport) -> SafetyNotice | None:
    if r.category.value == "none":
        return None
    return SafetyNotice(category=r.category.value, message=r.student_message, redactions=r.redactions)


def _record_blocked(
    db: Session, student_id: str, topic_id: str, question_id: str, concept_id: str, report: SafetyReport, tr: Tracer, parent_id: str | None, when: datetime | None
) -> tuple[StudentResponse, object]:
    """Data minimisation: only the redacted text and the category are kept."""
    row = StudentResponse(
        id=_uid(),
        parent_id=parent_id,
        student_id=student_id,
        topic_id=topic_id,
        question_id=question_id,
        concept_id=concept_id,
        kind="safety",
        answer=report.redacted_text[:300],
        payload={"safety": report.model_dump(mode="json", exclude={"redacted_text"})},
        created_at=when or datetime.now(timezone.utc),
    )
    db.add(row)
    db.flush()
    if report.notify_teacher:
        review_svc.add_item(
            db,
            kind="safety",
            category=report.category.value,
            severity=report.severity,
            student_id=student_id,
            excerpt=report.redacted_text,
            question_id=question_id,
            response_id=row.id,
            when=when,
        )
    trace = _save_trace(db, row, tr, when)
    db.commit()
    return row, trace


def _state(initial: StudentResponse) -> LearningState:
    return LearningState.model_validate(initial.payload["learning_state"])


def _save_state(initial: StudentResponse, st: LearningState, **extra) -> None:
    initial.payload = {**initial.payload, "learning_state": st.model_dump(mode="json"), **extra}


def _demo_answer(question, gq: GeneratedQuestion | None, is_demo: bool) -> str:
    if not (is_demo and gq and gq.source == "authored"):
        return ""
    tq = next((t for t in question.transfer_questions if t.id == gq.authored_id), None)
    return tq.demo_answer if tq else ""


async def submit(
    db: Session, harness: PedagogicalHarness, student_id: str, question_id: str, answer: str, session_id: str | None, *, when: datetime | None = None
) -> SubmitResponse:
    student = student_svc.get_student(db, student_id)
    pair = harness.curriculum.question(question_id)
    if not pair:
        raise NotFound(f"question {question_id} not found")
    topic, question = pair
    snap = student_svc.snapshot(db, student_id)

    result = await harness.run(topic, question, answer, snap)
    if isinstance(result, BlockedResult):
        _, trace = _record_blocked(db, student_id, topic.topic_id, question.id, question.concept, result.safety, result.trace, None, when)
        return SubmitResponse(trace_id=trace.id, mode=result.trace.mode, blocked=True, safety=_notice(result.safety), trace=result.trace.steps)

    v, d = result.verification, result.diagnosis
    xp = XP_ANSWER + (XP_REASONING if v.reasoning_correct else 0)
    concept = topic.concept(question.concept)
    st = sm.new_state(question.concept, concept.name, result.mastery.before)
    sm.apply_diagnosis(st, d, result.strategy.strategy)
    sm.transition(st, sm.phase_after_diagnosis(d), f"answer classified as {v.classification}")
    st.mastery = result.mastery.after

    resp = StudentResponse(
        id=_uid(),
        session_id=session_id,
        student_id=student_id,
        topic_id=topic.topic_id,
        question_id=question.id,
        concept_id=question.concept,
        kind="initial",
        answer=result.parsed_answer[:1000],  # PII already redacted by the safety layer
        answer_correct=v.answer_correct,
        reasoning_correct=v.reasoning_correct,
        misconception_id=d.misconception_id,
        misconception_type=d.type.value if d.type else None,
        strategy=result.strategy.strategy.value,
        transfer_question_id=result.transfer.id,
        resolved=not d.has_gap,
        mastery_before=result.mastery.before,
        mastery_after=result.mastery.after,
        payload={
            "verification": v.model_dump(mode="json"),
            "diagnosis": d.model_dump(mode="json"),
            "strategy": result.strategy.model_dump(mode="json"),
            "teaching": result.teaching.model_dump(mode="json"),
            "feedback": result.feedback.model_dump(mode="json"),
            "transfer_question": result.transfer.model_dump(mode="json"),
            "transfer_history": [],
            "quality": result.transfer_quality.model_dump(mode="json"),
            "missing_points": result.missing_points,
            "dont_know_streak": int(is_dont_know(normalize(result.parsed_answer))),
            "mastery_change": result.mastery.model_dump(mode="json"),
            "learning_state": st.model_dump(mode="json"),
            "safety": result.safety.model_dump(mode="json", exclude={"redacted_text"}),
            "xp": xp,
        },
        created_at=when or datetime.now(timezone.utc),
    )
    db.add(resp)
    if result.transfer.source == "generated":
        db.merge(
            QuestionRow(
                id=result.transfer.id,
                topic_id=topic.topic_id,
                concept_id=question.concept,
                prompt=result.transfer.prompt,
                kind="generated",
                payload=result.transfer.model_dump(mode="json"),
            )
        )
    student_svc.apply_mastery_change(db, student_id, result.mastery, when=when)
    student.xp += xp
    db.flush()
    trace = _save_trace(db, resp, result.trace, when)
    if session_id and (sess := db.get(LearningSession, session_id)):
        if question.id in sess.question_ids:
            sess.current_index = max(sess.current_index, sess.question_ids.index(question.id))
    db.commit()

    return SubmitResponse(
        interaction_id=resp.id,
        trace_id=trace.id,
        mode=result.trace.mode,
        safety=_notice(result.safety),
        learning_state=st,
        verification=v,
        diagnosis=d,
        feedback=result.feedback,
        teaching_strategy=result.strategy.strategy.value,
        strategy_reason=result.strategy.reason,
        teaching_response=result.teaching,
        transfer_question=PublicQuestion(**result.transfer.model_dump(include={"id", "concept", "prompt", "emoji", "source"})),
        question_quality=result.transfer_quality,
        mastery_before=result.mastery.before,
        mastery_after=result.mastery.after,
        mastery_change=result.mastery,
        trace=result.trace.steps,
        transfer_demo_answer=_demo_answer(question, result.transfer, student.is_demo),
    )


def _initial(db: Session, student_id: str, interaction_id: str) -> StudentResponse:
    r = db.get(StudentResponse, interaction_id)
    if not r or r.student_id != student_id or r.kind != "initial":
        raise NotFound(f"interaction {interaction_id} not found")
    return r


def _dialogue_row(initial: StudentResponse, text: str, teaching: TeachingResponse, turn: int, resolved: bool, misconception_id, when) -> StudentResponse:
    return StudentResponse(
        id=_uid(),
        parent_id=initial.id,
        session_id=initial.session_id,
        student_id=initial.student_id,
        topic_id=initial.topic_id,
        question_id=initial.question_id,
        concept_id=initial.concept_id,
        kind="dialogue",
        answer=text[:1000],
        misconception_id=misconception_id,
        strategy=teaching.strategy.value,
        resolved=resolved,
        payload={"teaching": teaching.model_dump(mode="json"), "turn": turn},
        created_at=when or datetime.now(timezone.utc),
    )


async def reply(db: Session, harness: PedagogicalHarness, student_id: str, interaction_id: str, message: str, *, when: datetime | None = None) -> ReplyResponse:
    initial = _initial(db, student_id, interaction_id)
    topic, question = harness.curriculum.question(initial.question_id)
    st = _state(initial)
    if st.phase not in (P.TEACHING, P.CLARIFYING):
        raise NotFound(f"interaction {interaction_id} is not waiting for a reply (state: {st.phase.value})")

    # safety layer on every student message
    tr = Tracer()
    report = harness._screen(tr, message, question.hints[0] if question.hints else None)
    if not report.allow_grading:
        _record_blocked(db, student_id, initial.topic_id, initial.question_id, initial.concept_id, report, tr, initial.id, when)
        return ReplyResponse(
            interaction_id=initial.id,
            turn=initial.dialogue_turns,
            resolved=False,
            ready_for_transfer=False,
            blocked=True,
            safety=_notice(report),
            learning_state=st,
            teaching_response=TeachingResponse(strategy=initial.strategy or "SOCRATIC_QUESTION", messages=[report.student_message]),
            trace=tr.steps,
        )
    message = report.redacted_text
    turn = initial.dialogue_turns + 1

    if st.phase == P.CLARIFYING:
        snap = student_svc.snapshot(db, student_id)
        # reply first: a long first answer is cut at MAX_ANSWER_CHARS and must not hide the clarification
        re = await harness.run(topic, question, f"{message}. {initial.answer}", snap, reassess=True)
        tr.steps.extend(re.trace.steps)
        d = re.diagnosis
        analysis = None
        deferred = False
        if d.needs_clarification:
            if turn >= MAX_TURNS:
                deferred = True
                teaching = TeachingResponse(
                    strategy="CLARIFY",
                    messages=[
                        "Thanks for explaining! 🙏",
                        "This one is tricky for me to judge, and I don't want to tell you something that might not fit your idea.",
                        "I've asked your teacher to look at it with you. Let's carry on with the next question for now.",
                    ],
                )
                sm.transition(st, P.DEFERRED, "still unclear after clarification → teacher review")
                st.deferred_reason = "Answer could not be judged after clarification"
                review_svc.add_item(
                    db,
                    kind="deferred",
                    category="unclear",
                    severity="medium",
                    student_id=student_id,
                    excerpt=f"{initial.answer} / {message}",
                    question_id=initial.question_id,
                    response_id=initial.id,
                    when=when,
                )
            else:
                teaching = TeachingResponse(
                    strategy="CLARIFY",
                    messages=["Thanks! I'm still not quite sure what you mean. 🤔"],
                    follow_up=(question.hints[1] if len(question.hints) > 1 else "Which one do you choose, and what is the reason? Use “because …”."),
                )
                sm.transition(st, P.CLARIFYING, "still unclear")
        else:
            teaching, analysis = re.teaching, re.feedback
            sm.apply_diagnosis(st, d, re.strategy.strategy)
            nxt = sm.phase_after_diagnosis(d)
            sm.transition(st, nxt, f"clarified → {d.classification}")
            initial.misconception_id = d.misconception_id
            initial.misconception_type = d.type.value if d.type else None
            initial.strategy = re.strategy.strategy.value
            initial.payload = {
                **initial.payload,
                "diagnosis": d.model_dump(mode="json"),
                "verification": re.verification.model_dump(mode="json"),
                "teaching": teaching.model_dump(mode="json"),
                "missing_points": re.missing_points,
            }
            if nxt == P.TRANSFER:
                teaching.ready_for_transfer = True
        row = _dialogue_row(initial, message, teaching, turn, not d.needs_clarification, d.misconception_id, when)
        db.add(row)
        # a clarified answer starts a fresh teaching dialogue
        initial.dialogue_turns = 0 if st.phase == P.TEACHING else turn
        streak = initial.payload.get("dont_know_streak", 0) + 1 if is_dont_know(normalize(message)) else 0
        _save_state(initial, st, dont_know_streak=streak)
        db.flush()
        _save_trace(db, row, tr, when)
        db.commit()
        return ReplyResponse(
            interaction_id=initial.id,
            turn=turn,
            resolved=not d.needs_clarification,
            ready_for_transfer=st.phase == P.TRANSFER,
            deferred=deferred,
            safety=_notice(report),
            learning_state=st,
            analysis=analysis,
            teaching_response=teaching,
            trace=tr.steps,
        )

    # TEACHING phase: check whether the targeted idea has been repaired
    last_strategy = initial.payload.get("last_strategy") or initial.strategy
    outcome, dtr = harness.reply(topic, question, message, turn, initial.misconception_id, last_strategy, initial.payload.get("missing_points", []))
    tr.steps.extend(dtr.steps)
    ready = outcome.response.ready_for_transfer or turn >= MAX_TURNS
    if ready:
        sm.transition(st, P.TRANSFER, "idea repaired in dialogue" if outcome.resolved else "dialogue limit reached → key idea stated")
    else:
        sm.transition(st, P.TEACHING, f"another angle: {outcome.response.strategy.value.lower()}")
        st.intervention = outcome.response.strategy
    row = _dialogue_row(initial, message, outcome.response, turn, outcome.resolved, initial.misconception_id if outcome.misconception_reappeared else None, when)
    db.add(row)
    initial.dialogue_turns = turn
    initial.resolved = initial.resolved or outcome.resolved
    streak = initial.payload.get("dont_know_streak", 0) + 1 if outcome.dont_know else 0
    _save_state(initial, st, last_strategy=outcome.response.strategy.value, dont_know_streak=streak)
    db.flush()
    _save_trace(db, row, tr, when)
    db.commit()
    return ReplyResponse(
        interaction_id=initial.id,
        turn=turn,
        resolved=outcome.resolved,
        ready_for_transfer=ready,
        safety=_notice(report),
        learning_state=st,
        teaching_response=outcome.response,
        trace=tr.steps,
    )


async def transfer(db: Session, harness: PedagogicalHarness, student_id: str, interaction_id: str, answer: str, *, when: datetime | None = None) -> TransferResponse:
    student = student_svc.get_student(db, student_id)
    initial = _initial(db, student_id, interaction_id)
    topic, question = harness.curriculum.question(initial.question_id)
    st = _state(initial)
    if st.phase in (P.TEACHING, P.RETEACH):
        sm.transition(st, P.TRANSFER, "student moved on to the question back")
    if st.phase != P.TRANSFER:
        raise NotFound(f"interaction {interaction_id} is not at the transfer step (state: {st.phase.value})")
    tq = GeneratedQuestion.model_validate(initial.payload["transfer_question"])
    history = list(initial.payload.get("transfer_history", []))
    snap = student_svc.snapshot(db, student_id)
    attempt = st.transfer_attempts + 1

    streak = initial.payload.get("dont_know_streak", 0)
    result = await harness.run_transfer(
        topic, question, tq, answer, snap, initial.misconception_id, attempt, set(history) | snap.seen_transfer_ids, dont_know_streak=streak
    )
    if isinstance(result, BlockedResult):
        _, trace = _record_blocked(db, student_id, initial.topic_id, initial.question_id, initial.concept_id, result.safety, result.trace, initial.id, when)
        _save_state(initial, st)
        db.commit()
        return TransferResponse(
            interaction_id=initial.id, trace_id=trace.id, blocked=True, safety=_notice(result.safety), learning_state=st, attempt=st.transfer_attempts, trace=result.trace.steps
        )

    v = result.verification
    xp = XP_ANSWER + (XP_TRANSFER if result.confirmed else 0)
    row = StudentResponse(
        id=_uid(),
        parent_id=initial.id,
        session_id=initial.session_id,
        student_id=student_id,
        topic_id=initial.topic_id,
        question_id=initial.question_id,
        concept_id=initial.concept_id,
        kind="transfer",
        answer=result.safety.redacted_text[:1000],
        answer_correct=v.answer_correct,
        reasoning_correct=v.reasoning_correct,
        misconception_id=v.misconceptions[0].id if v.misconceptions else None,
        misconception_type=v.misconceptions[0].type.value if v.misconceptions else None,
        transfer_question_id=tq.id,
        resolved=result.confirmed,
        mastery_before=result.mastery.before,
        mastery_after=result.mastery.after,
        payload={
            "prompt": tq.prompt,
            "source": tq.source,
            "attempt": attempt,
            "verification": v.model_dump(mode="json"),
            "feedback": result.feedback,
            "reteach": result.reteach.model_dump(mode="json") if result.reteach else None,
            "mastery_change": result.mastery.model_dump(mode="json"),
            "xp": xp,
        },
        created_at=when or datetime.now(timezone.utc),
    )
    db.add(row)
    mrow = student_svc.apply_mastery_change(db, student_id, result.mastery, verified=result.confirmed, when=when)
    student.xp += xp

    st.transfer_attempts = attempt
    st.mastery = result.mastery.after
    st.classification = v.classification
    if result.diagnosis is not None:  # re-teach targets what this transfer answer revealed
        st.misconception_id = result.diagnosis.misconception_id
        st.misconception_label = result.diagnosis.label or None
    nxt = P.REVISIT if result.stuck else sm.phase_after_transfer(result.confirmed, result.mastery.after, attempt)
    trigger = {
        P.MASTERED: "transfer verified · mastery threshold reached",
        P.VERIFIED: "transfer verified · mastery still growing",
        P.RETEACH: "transfer failed → re-teach + second question back",
        P.REVISIT: "kept saying “I don't know” → key idea shown, teacher flagged" if result.stuck else "second transfer failed → revisit later",
    }[nxt]
    sm.transition(st, nxt, trigger)
    streak = streak + 1 if result.dont_know else 0
    extra = {"transfer_history": [*history, tq.id], "dont_know_streak": streak}
    if nxt == P.RETEACH and result.next_question:
        extra["transfer_question"] = result.next_question.model_dump(mode="json")
        st.intervention = result.reteach.strategy if result.reteach else st.intervention
    persistent = initial.misconception_id and any(m.id == initial.misconception_id for m in v.misconceptions)
    if result.stuck:
        review_svc.add_item(
            db,
            kind="stuck",
            category="repeated_dont_know",
            severity="medium",
            student_id=student_id,
            excerpt=result.safety.redacted_text,
            question_id=initial.question_id,
            response_id=initial.id,
            when=when,
        )
    if nxt == P.REVISIT and persistent:
        review_svc.add_item(
            db,
            kind="persistent_misconception",
            category=initial.misconception_id,
            severity="medium",
            student_id=student_id,
            excerpt=result.safety.redacted_text,
            question_id=initial.question_id,
            response_id=initial.id,
            when=when,
        )
    c = topic.concept(question.concept)
    rows = student_svc.mastery_rows(db, student_id)
    prereq = [rows[p].mastery_score if p in rows else 0.0 for p in (c.prerequisites if c else [])]
    status = mastery_model.status_for(mrow.mastery_score, mrow.attempt_count, prereq, mrow.verified_count)
    st.mastery_status = status.value
    _save_state(initial, st, **extra)
    db.flush()
    trace = _save_trace(db, row, result.trace, when)
    db.commit()

    return TransferResponse(
        interaction_id=initial.id,
        trace_id=trace.id,
        safety=_notice(result.safety),
        learning_state=st,
        next_state=nxt.value,
        mastery_confirmed=result.confirmed,
        mastery_before=result.mastery.before,
        mastery_after=result.mastery.after,
        mastery_change=result.mastery,
        concept_status=status,
        feedback=result.feedback,
        verification=v,
        teaching_response=result.reteach if nxt == P.RETEACH else None,
        next_transfer_question=(
            PublicQuestion(**result.next_question.model_dump(include={"id", "concept", "prompt", "emoji", "source"}))
            if nxt == P.RETEACH and result.next_question
            else None
        ),
        next_transfer_demo_answer=_demo_answer(question, result.next_question, student.is_demo) if nxt == P.RETEACH else "",
        attempt=attempt,
        xp_earned=xp,
        trace=result.trace.steps,
    )
