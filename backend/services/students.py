"""Student state: mastery reads/writes, snapshots for the harness, dashboard assembly."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from curriculum.loader import Curriculum
from harness import mastery as mastery_model
from harness.context import StudentSnapshot
from models.tables import MasteryEvent, Student, StudentMastery, StudentResponse
from schemas.api import (
    ActivityItem,
    ConceptNode,
    DashboardResponse,
    GraphEdge,
    HistoryPoint,
    MisconceptionCard,
    NextUp,
    StudentMasteryResponse,
    StudentProfile,
    TodayStats,
    TopicDetail,
    TopicProgress,
    TopicSummary,
)
from schemas.curriculum import Topic
from schemas.enums import MasteryStatus
from schemas.harness import MasteryChange

SGT = ZoneInfo("Asia/Singapore")
LEVEL_AGE = {"Primary 4": 10, "Primary 5": 11, "Primary 6": 12}


class NotFound(LookupError):
    pass


def get_student(db: Session, student_id: str) -> Student:
    s = db.get(Student, student_id)
    if not s:
        raise NotFound(f"student {student_id} not found")
    return s


def profile(s: Student) -> StudentProfile:
    return StudentProfile(
        id=s.id, display_name=s.display_name, level=s.level, class_name=s.class_name, avatar=s.avatar, streak_days=s.streak_days, xp=s.xp, is_demo=s.is_demo
    )


def mastery_rows(db: Session, student_id: str) -> dict[str, StudentMastery]:
    rows = db.scalars(select(StudentMastery).where(StudentMastery.student_id == student_id)).all()
    return {r.concept_id: r for r in rows}


def snapshot(db: Session, student_id: str) -> StudentSnapshot:
    s = get_student(db, student_id)
    rows = mastery_rows(db, student_id)
    responses = db.scalars(
        select(StudentResponse).where(StudentResponse.student_id == student_id).order_by(StudentResponse.created_at)
    ).all()
    history: Counter[str] = Counter()
    last_strategy: dict[str, str] = {}
    seen: set[str] = set()
    for r in responses:
        if r.misconception_id and r.kind in ("initial", "transfer"):
            history[r.misconception_id] += 1
            if r.strategy:
                last_strategy[r.misconception_id] = r.strategy
        if r.kind == "transfer" and r.transfer_question_id:
            seen.add(r.transfer_question_id)
    return StudentSnapshot(
        student_id=s.id,
        display_name=s.display_name,
        level=s.level,
        age=LEVEL_AGE.get(s.level, 11),
        mastery={k: v.mastery_score for k, v in rows.items()},
        misconception_history=dict(history),
        last_strategy_for=last_strategy,
        seen_transfer_ids=seen,
    )


def apply_mastery_change(db: Session, student_id: str, change: MasteryChange, *, verified: bool = False, when: datetime | None = None) -> StudentMastery:
    row = db.scalar(select(StudentMastery).where(StudentMastery.student_id == student_id, StudentMastery.concept_id == change.concept_id))
    if row is None:
        row = StudentMastery(student_id=student_id, concept_id=change.concept_id, mastery_score=0.0, attempt_count=0, verified_count=0)
        db.add(row)
    row.mastery_score = change.after
    row.attempt_count = (row.attempt_count or 0) + 1
    if verified:
        row.verified_count = (row.verified_count or 0) + 1
    row.last_updated = when or datetime.now(timezone.utc)
    db.add(
        MasteryEvent(
            student_id=student_id,
            concept_id=change.concept_id,
            before=change.before,
            after=change.after,
            evidence=change.evidence,
            reason=change.reason[:250],
            created_at=when or datetime.now(timezone.utc),
        )
    )
    return row


# ----------------------------------------------------------------- concept views
def concept_nodes(curriculum: Curriculum, topic: Topic, rows: dict[str, StudentMastery] | None) -> list[ConceptNode]:
    rows = rows or {}
    miscs = defaultdict(list)
    for m in topic.misconceptions:
        miscs[m.concept].append(m.label)
    nodes = []
    for c in topic.concepts:
        r = rows.get(c.id)
        score = r.mastery_score if r else 0.0
        attempts = r.attempt_count if r else 0
        prereq_scores = [rows[p].mastery_score if p in rows else 0.0 for p in c.prerequisites]
        nodes.append(
            ConceptNode(
                id=c.id,
                topic_id=topic.topic_id,
                name=c.name,
                emoji=c.emoji,
                summary=c.summary,
                learning_objective=c.learning_objective,
                key_ideas=c.key_ideas,
                prerequisites=c.prerequisites,
                position=c.position,
                mastery=round(score, 4),
                status=mastery_model.status_for(score, attempts, prereq_scores, r.verified_count if r else 0),
                attempts=attempts,
                verified=r.verified_count if r else 0,
                misconceptions=miscs[c.id],
                mastery_criterion=c.mastery_criterion,
            )
        )
    return nodes


def topic_progress(topic: Topic, nodes: list[ConceptNode]) -> TopicProgress:
    return TopicProgress(
        topic_id=topic.topic_id,
        name=topic.name,
        emoji=topic.emoji,
        color=topic.color,
        mastery=round(sum(n.mastery for n in nodes) / max(1, len(nodes)), 4),
        mastered=sum(n.status == MasteryStatus.MASTERED for n in nodes),
        learning=sum(n.status == MasteryStatus.LEARNING for n in nodes),
        total=len(nodes),
    )


def topic_summary(topic: Topic, mastery: float | None = None) -> TopicSummary:
    return TopicSummary(
        topic_id=topic.topic_id,
        name=topic.name,
        subject=topic.subject,
        level=topic.level,
        emoji=topic.emoji,
        color=topic.color,
        tagline=topic.tagline,
        description=topic.description.strip(),
        concept_count=len(topic.concepts),
        question_count=len(topic.questions),
        mastery=mastery,
        theme=topic.theme,
        syllabus_ref=topic.syllabus_ref,
    )


def topic_detail(curriculum: Curriculum, topic: Topic, rows: dict[str, StudentMastery] | None) -> TopicDetail:
    nodes = concept_nodes(curriculum, topic, rows)
    prog = topic_progress(topic, nodes) if rows is not None else None
    base = topic_summary(topic, prog.mastery if prog else None)
    edges = [GraphEdge(source=p, target=c.id) for c in topic.concepts for p in c.prerequisites]
    miscs = [
        MisconceptionCard(id=m.id, label=m.label, statement=m.statement, corrective_target=m.corrective_target, concept=m.concept, type=m.type.value)
        for m in topic.misconceptions
    ]
    return TopicDetail(**base.model_dump(), concepts=nodes, edges=edges, misconceptions=miscs)


def student_mastery(db: Session, curriculum: Curriculum, student_id: str) -> StudentMasteryResponse:
    get_student(db, student_id)
    rows = mastery_rows(db, student_id)
    all_nodes: list[ConceptNode] = []
    topics = []
    for t in curriculum.topics:
        nodes = concept_nodes(curriculum, t, rows)
        all_nodes.extend(nodes)
        topics.append(topic_progress(t, nodes))
    return StudentMasteryResponse(
        student_id=student_id,
        concept_mastery={n.id: n.mastery for n in all_nodes},
        concepts=all_nodes,
        topics=topics,
    )


# ----------------------------------------------------------------- dashboard
def _result_label(r: StudentResponse) -> str:
    if r.kind == "transfer":
        return "verified" if (r.answer_correct and r.reasoning_correct) else "needs_practice"
    if r.answer_correct and r.reasoning_correct:
        return "verified"
    return "learning" if (r.answer_correct or r.misconception_id) else "needs_practice"


BADGES = [
    ("first_steps", "First Steps", "seedling", "Answered your first question"),
    ("deep_thinker", "Deep Thinker", "brain", "Explained your reasoning 5 times"),
    ("myth_buster", "Myth Buster", "magnifying_glass", "Fixed a misconception"),
    ("transfer_pro", "Transfer Pro", "rocket", "Verified understanding in a new situation"),
    ("streak_3", "On Fire", "fire", "3-day learning streak"),
    ("master", "Concept Master", "trophy", "Mastered 5 concepts"),
]


def dashboard(db: Session, curriculum: Curriculum, student_id: str) -> DashboardResponse:
    s = get_student(db, student_id)
    rows = mastery_rows(db, student_id)
    topics_nodes = {t.topic_id: concept_nodes(curriculum, t, rows) for t in curriculum.topics}
    progress = [topic_progress(t, topics_nodes[t.topic_id]) for t in curriculum.topics]

    responses = db.scalars(
        select(StudentResponse).where(StudentResponse.student_id == student_id).order_by(StudentResponse.created_at.desc())
    ).all()
    main = [r for r in responses if r.kind in ("initial", "transfer")]

    # current topic = most recently practised, else the first topic
    current_id = main[0].topic_id if main else curriculum.topics[0].topic_id
    current = next(p for p in progress if p.topic_id == current_id)

    today = datetime.now(SGT).date()
    todays = [r for r in main if r.created_at.replace(tzinfo=r.created_at.tzinfo or timezone.utc).astimezone(SGT).date() == today]
    verified_today = sum(1 for r in todays if r.kind == "transfer" and r.answer_correct and r.reasoning_correct)

    concept_name = {c.id: c.name for _, c in curriculum.all_concepts()}
    recent = []
    for r in main[:8]:
        pair = curriculum.question(r.question_id)
        prompt = pair[1].prompt if pair else r.payload.get("prompt", "")
        if r.kind == "transfer":
            prompt = r.payload.get("prompt", prompt)
        recent.append(
            ActivityItem(
                id=r.id,
                kind=r.kind,
                topic_id=r.topic_id,
                concept_id=r.concept_id,
                concept_name=concept_name.get(r.concept_id, r.concept_id),
                question_prompt=prompt,
                result=_result_label(r),
                mastery_before=r.mastery_before,
                mastery_after=r.mastery_after,
                created_at=r.created_at,
            )
        )

    # next up: lowest-mastery unlocked concept in the current topic
    candidates = [n for n in topics_nodes[current_id] if n.status not in (MasteryStatus.MASTERED, MasteryStatus.LOCKED)]
    candidates.sort(key=lambda n: (n.status != MasteryStatus.LEARNING, n.mastery))
    nxt = None
    if candidates:
        n = candidates[0]
        reason = "You're close — one verified answer could lock it in!" if n.mastery >= 0.45 else "This one needs a bit more practice."
        nxt = NextUp(topic_id=current_id, concept_id=n.id, concept_name=n.name, reason=reason)

    # Curio insight
    misc = Counter(r.misconception_id for r in main if r.misconception_id)
    if misc:
        mid, _ = misc.most_common(1)[0]
        m = next((m for t in curriculum.topics for m in t.misconceptions if m.id == mid), None)
        insight = f"You're getting better at explaining *why*. Watch out for this sneaky idea: “{m.statement}”" if m else ""
    else:
        insight = "Great habit: you explain your reasoning, not just the answer. Keep it up!"

    # mastery history (last 14 days) of the current topic
    events = db.scalars(select(MasteryEvent).where(MasteryEvent.student_id == student_id).order_by(MasteryEvent.created_at)).all()
    topic_concepts = {c.id for c in curriculum.topic(current_id).concepts}
    state = {cid: 0.0 for cid in topic_concepts}
    # reconstruct start state by rewinding events from current values
    for cid in topic_concepts:
        state[cid] = rows[cid].mastery_score if cid in rows else 0.0
    for e in reversed(events):
        if e.concept_id in topic_concepts:
            state[e.concept_id] = e.before
    by_day: dict[str, list[MasteryEvent]] = defaultdict(list)
    for e in events:
        by_day[e.created_at.replace(tzinfo=e.created_at.tzinfo or timezone.utc).astimezone(SGT).date().isoformat()].append(e)
    history = []
    for i in range(13, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        for e in by_day.get(d, []):
            if e.concept_id in topic_concepts:
                state[e.concept_id] = e.after
        history.append(HistoryPoint(date=d, mastery=round(sum(state.values()) / max(1, len(state)), 4), answers=len(by_day.get(d, []))))

    n_answers = len(main)
    fixed = sum(1 for r in responses if r.kind == "dialogue" and r.resolved)
    transfers_ok = sum(1 for r in main if r.kind == "transfer" and r.answer_correct and r.reasoning_correct)
    reasoning_ok = sum(1 for r in main if r.reasoning_correct)
    mastered = sum(p.mastered for p in progress)
    earned = {
        "first_steps": n_answers >= 1,
        "deep_thinker": reasoning_ok >= 5,
        "myth_buster": fixed >= 1,
        "transfer_pro": transfers_ok >= 1,
        "streak_3": s.streak_days >= 3,
        "master": mastered >= 5,
    }
    badges = [{"id": b, "name": n, "emoji": e, "description": d, "earned": earned[b]} for b, n, e, d in BADGES]

    return DashboardResponse(
        student=profile(s),
        topics=progress,
        current_topic=current,
        current_concepts=topics_nodes[current_id],
        today=TodayStats(questions_answered=len(todays), verified=verified_today, xp_today=sum(r.payload.get("xp", 0) for r in todays)),
        recent_activity=recent,
        next_up=nxt,
        insight=insight,
        history=history,
        badges=badges,
    )
