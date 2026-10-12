"""Teacher analytics (spec §13) and agent-trace inspection (spec §22)."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from curriculum.loader import Curriculum
from harness.mastery import LEARNING_AT, MASTERED_AT
from models.tables import AgentTrace, ReviewQueueItem, Student, StudentMastery, StudentResponse
from schemas.api import (
    ClassAnalytics,
    DayStat,
    DialogueTurn,
    HeatmapConcept,
    MisconceptionStat,
    StrategyStat,
    StudentRow,
    TopicStat,
    TraceDetail,
    TraceSummary,
)
from schemas.harness import TraceStep
from services.students import SGT, NotFound


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def class_analytics(db: Session, curriculum: Curriculum, class_name: str | None = None) -> ClassAnalytics:
    students = db.scalars(select(Student)).all()
    if class_name:
        students = [s for s in students if s.class_name == class_name]
    ids = {s.id for s in students}
    responses = [r for r in db.scalars(select(StudentResponse)).all() if r.student_id in ids]
    mastery = [m for m in db.scalars(select(StudentMastery)).all() if m.student_id in ids]

    main = [r for r in responses if r.kind in ("initial", "transfer")]
    initials = [r for r in responses if r.kind == "initial"]
    transfers = [r for r in responses if r.kind == "transfer"]
    verified = [r for r in transfers if r.answer_correct and r.reasoning_correct]

    # misconceptions
    by_misc: dict[str, list[StudentResponse]] = defaultdict(list)
    for r in main:
        if r.misconception_id:
            by_misc[r.misconception_id].append(r)
    initial_by_id = {r.id: r for r in initials}
    confirmed_parents = {r.parent_id for r in verified}
    concept_name = {c.id: c.name for _, c in curriculum.all_concepts()}
    top = []
    for mid, rs in by_misc.items():
        topic = next((t for t in curriculum.topics if t.misconception(mid)), None)
        if not topic:
            continue
        m = topic.misconception(mid)
        parents = [r for r in rs if r.kind == "initial"]
        resolved = sum(1 for r in parents if r.id in confirmed_parents)
        top.append(
            MisconceptionStat(
                id=mid,
                label=m.label,
                statement=m.statement,
                topic_id=topic.topic_id,
                topic_name=topic.name,
                concept_id=m.concept,
                concept_name=concept_name.get(m.concept, m.concept),
                students=len({r.student_id for r in rs}),
                occurrences=len(rs),
                resolved_rate=round(resolved / len(parents), 3) if parents else 0.0,
            )
        )
    top.sort(key=lambda x: (-x.students, -x.occurrences))

    # topics
    m_by_student: dict[str, dict[str, float]] = defaultdict(dict)
    for m in mastery:
        m_by_student[m.student_id][m.concept_id] = m.mastery_score
    topic_stats = []
    for t in curriculum.topics:
        scores = [m_by_student[s.id].get(c.id, 0.0) for s in students for c in t.concepts]
        topic_stats.append(
            TopicStat(
                topic_id=t.topic_id,
                name=t.name,
                color=t.color,
                emoji=t.emoji,
                avg_mastery=round(sum(scores) / max(1, len(scores)), 4),
                mastered=sum(x >= MASTERED_AT for x in scores),
                learning=sum(LEARNING_AT <= x < MASTERED_AT for x in scores),
                needs_practice=sum(x < LEARNING_AT for x in scores),
            )
        )

    # strategy effectiveness = share of taught interactions later verified by transfer
    strat: dict[str, list[bool]] = defaultdict(list)
    for r in initials:
        if r.strategy and r.strategy != "TRANSFER_EXAMPLE":
            strat[r.strategy].append(r.id in confirmed_parents)
    strategies = sorted(
        (StrategyStat(strategy=k, uses=len(v), success_rate=round(sum(v) / len(v), 3)) for k, v in strat.items()),
        key=lambda s: -s.uses,
    )

    # activity (last 14 days, SGT)
    today = datetime.now(SGT).date()
    day_counts: Counter[str] = Counter()
    day_verified: Counter[str] = Counter()
    for r in main:
        d = _aware(r.created_at).astimezone(SGT).date().isoformat()
        day_counts[d] += 1
    for r in verified:
        day_verified[_aware(r.created_at).astimezone(SGT).date().isoformat()] += 1
    activity = [
        DayStat(date=(today - timedelta(days=i)).isoformat(), answers=day_counts[(today - timedelta(days=i)).isoformat()], verified=day_verified[(today - timedelta(days=i)).isoformat()])
        for i in range(13, -1, -1)
    ]
    active_today = len({r.student_id for r in main if _aware(r.created_at).astimezone(SGT).date() == today})

    # answer vs reasoning (the core Curio insight)
    avr = Counter()
    for r in initials:
        key = ("answer_ok" if r.answer_correct else "answer_wrong") + ("_reasoning_ok" if r.reasoning_correct else "_reasoning_wrong")
        avr[key] += 1

    # roster
    all_concepts = [c for _, c in curriculum.all_concepts()]
    roster = []
    for s in students:
        rs = [r for r in main if r.student_id == s.id]
        sc = m_by_student[s.id]
        miscs = Counter(r.misconception_id for r in rs if r.misconception_id)
        top_m = None
        if miscs:
            mid = miscs.most_common(1)[0][0]
            mm = next((t.misconception(mid) for t in curriculum.topics if t.misconception(mid)), None)
            top_m = mm.label if mm else mid
        roster.append(
            StudentRow(
                id=s.id,
                display_name=s.display_name,
                avatar=s.avatar,
                avg_mastery=round(sum(sc.get(c.id, 0.0) for c in all_concepts) / max(1, len(all_concepts)), 4),
                answered=len(rs),
                verified=sum(1 for r in rs if r.kind == "transfer" and r.answer_correct and r.reasoning_correct),
                top_misconception=top_m,
                scores={c.id: round(sc.get(c.id, 0.0), 3) for c in all_concepts},
            )
        )
    roster.sort(key=lambda r: r.avg_mastery)

    classification_mix = Counter(r.payload.get("verification", {}).get("classification", "incorrect") for r in initials)
    safety_events = Counter(r.payload.get("safety", {}).get("category", "none") for r in responses if r.kind == "safety")
    safety_events.update(
        r.payload.get("safety", {}).get("category") for r in initials if r.payload.get("safety", {}).get("category") == "pii"
    )
    loop_outcomes = Counter(r.payload.get("learning_state", {}).get("phase", "attempt") for r in initials)
    open_reviews = sum(1 for q in db.scalars(select(ReviewQueueItem).where(ReviewQueueItem.status == "open")) if q.student_id in ids)

    all_scores = [x for s in students for x in [m_by_student[s.id].get(c.id, 0.0) for c in all_concepts]]
    return ClassAnalytics(
        class_name=class_name or (students[0].class_name if students else "Class"),
        students=len(students),
        questions_answered=len(main),
        verified_mastery_rate=round(len(verified) / max(1, len(transfers)), 4),
        avg_mastery=round(sum(all_scores) / max(1, len(all_scores)), 4),
        active_today=active_today,
        answer_vs_reasoning=dict(avr),
        top_misconceptions=top[:8],
        topics=topic_stats,
        strategies=strategies,
        activity=activity,
        heatmap_concepts=[HeatmapConcept(id=c.id, name=c.name, topic_id=t.topic_id) for t, c in curriculum.all_concepts()],
        roster=roster,
        classification_mix=dict(classification_mix),
        safety_events=dict(safety_events),
        open_reviews=open_reviews,
        loop_outcomes=dict(loop_outcomes),
    )


# ----------------------------------------------------------------- traces
def _summary(db: Session, curriculum: Curriculum, initial: StudentResponse, trace: AgentTrace, student: Student, transfer: StudentResponse | None) -> TraceSummary:
    pair = curriculum.question(initial.question_id)
    topic, q = pair if pair else (None, None)
    c = topic.concept(initial.concept_id) if topic else None
    m = topic.misconception(initial.misconception_id) if (topic and initial.misconception_id) else None
    diag = initial.payload.get("diagnosis", {})
    return TraceSummary(
        id=trace.id,
        interaction_id=initial.id,
        student_id=student.id,
        student_name=student.display_name,
        avatar=student.avatar,
        topic_id=initial.topic_id,
        concept_id=initial.concept_id,
        concept_name=c.name if c else initial.concept_id,
        question_prompt=q.prompt if q else "",
        answer=initial.answer,
        answer_correct=initial.answer_correct,
        reasoning_correct=initial.reasoning_correct,
        misconception_label=(m.label if m else diag.get("label")) or None,
        strategy=initial.strategy,
        mastery_before=initial.mastery_before,
        mastery_after=transfer.mastery_after if transfer else initial.mastery_after,
        transfer_confirmed=(bool(transfer.answer_correct and transfer.reasoning_correct) if transfer else None),
        mode=trace.mode,
        total_ms=trace.total_ms + (0 if not transfer else 0),
        created_at=initial.created_at,
    )


def _children(db: Session, initial_id: str) -> list[StudentResponse]:
    return db.scalars(select(StudentResponse).where(StudentResponse.parent_id == initial_id).order_by(StudentResponse.created_at)).all()


def list_traces(db: Session, curriculum: Curriculum, limit: int = 30, student_id: str | None = None) -> list[TraceSummary]:
    stmt = select(AgentTrace).where(AgentTrace.kind == "initial").order_by(AgentTrace.created_at.desc()).limit(limit)
    if student_id:
        stmt = stmt.where(AgentTrace.student_id == student_id)
    out = []
    for t in db.scalars(stmt).all():
        initial = db.get(StudentResponse, t.response_id)
        student = db.get(Student, t.student_id)
        if not initial or not student:
            continue
        transfer = next((c for c in reversed(_children(db, initial.id)) if c.kind == "transfer"), None)
        out.append(_summary(db, curriculum, initial, t, student, transfer))
    return out


def trace_detail(db: Session, curriculum: Curriculum, trace_id: str) -> TraceDetail:
    t = db.get(AgentTrace, trace_id)
    if not t:
        raise NotFound(f"trace {trace_id} not found")
    initial = db.get(StudentResponse, t.response_id)
    if initial.kind != "initial" and initial.parent_id:
        initial = db.get(StudentResponse, initial.parent_id)
        t = db.scalar(select(AgentTrace).where(AgentTrace.response_id == initial.id))
    student = db.get(Student, initial.student_id)
    children = _children(db, initial.id)
    transfers = [c for c in children if c.kind == "transfer"]
    transfer = transfers[-1] if transfers else None
    transfer_steps = []
    for tr_row in transfers:
        tt = db.scalar(select(AgentTrace).where(AgentTrace.response_id == tr_row.id))
        if tt:
            transfer_steps.extend(tt.steps)

    p = initial.payload
    teaching = p.get("teaching", {})
    dialogue: list[DialogueTurn] = [
        DialogueTurn(role="curio", text=msg, strategy=teaching.get("strategy")) for msg in teaching.get("messages", [])
    ]
    if teaching.get("follow_up"):
        dialogue.append(DialogueTurn(role="curio", text=teaching["follow_up"], strategy=teaching.get("strategy")))
    for c in children:
        if c.kind == "transfer":
            dialogue.append(DialogueTurn(role="curio", text=f"🚀 Question back: {c.payload.get('prompt', '')}"))
            dialogue.append(DialogueTurn(role="student", text=c.answer))
            dialogue.append(DialogueTurn(role="curio", text=c.payload.get("feedback", "")))
            rt = c.payload.get("reteach") or {}
            for msg in rt.get("messages", []):
                dialogue.append(DialogueTurn(role="curio", text=msg, strategy=rt.get("strategy")))
            continue
        if c.kind == "safety":
            dialogue.append(DialogueTurn(role="student", text=c.answer))
            dialogue.append(DialogueTurn(role="curio", text=f"🛡️ Safety layer: {c.payload.get('safety', {}).get('category', '')} — not graded"))
            continue
        if c.kind != "dialogue":
            continue
        dialogue.append(DialogueTurn(role="student", text=c.answer))
        ct = c.payload.get("teaching", {})
        for msg in ct.get("messages", []):
            dialogue.append(DialogueTurn(role="curio", text=msg, strategy=ct.get("strategy")))
        if ct.get("follow_up"):
            dialogue.append(DialogueTurn(role="curio", text=ct["follow_up"], strategy=ct.get("strategy")))

    base = _summary(db, curriculum, initial, t, student, transfer)
    return TraceDetail(
        **base.model_dump(),
        verification=p.get("verification", {}),
        diagnosis=p.get("diagnosis", {}),
        feedback=p.get("feedback", {}),
        teaching={**teaching, "reason": p.get("strategy", {}).get("reason", "")},
        dialogue=dialogue,
        transfer_question={k: v for k, v in p.get("transfer_question", {}).items() if k in ("id", "prompt", "emoji", "source")} or None,
        transfer_answer=transfer.answer if transfer else None,
        transfer_feedback=None,
        transfer_verification=transfer.payload.get("verification") if transfer else None,
        final_mastery=transfer.mastery_after if transfer else initial.mastery_after,
        steps=[TraceStep.model_validate(s) for s in t.steps],
        transfer_steps=[TraceStep.model_validate(s) for s in transfer_steps],
        learning_state=p.get("learning_state"),
        transfer_attempts=[
            {
                "attempt": c.payload.get("attempt", i + 1),
                "prompt": c.payload.get("prompt", ""),
                "source": c.payload.get("source", "authored"),
                "answer": c.answer,
                "confirmed": bool(c.answer_correct and c.reasoning_correct),
                "feedback": c.payload.get("feedback", ""),
                "mastery_before": c.mastery_before,
                "mastery_after": c.mastery_after,
            }
            for i, c in enumerate(transfers)
        ],
    )
