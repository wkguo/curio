"""PedagogicalHarness (spec §5) — one orchestrator, modular steps, full trace.

    Verify → Validate → Teach → Question Back → Confirm Understanding

Each step is timed and recorded as a TraceStep (spec §22). Every step has a
deterministic rule path, so the loop always completes even when the LLM is down
(spec §25); in that case the step is marked mode="fallback" in the trace.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field

from config import get_settings
from curriculum.loader import Curriculum
from curriculum.retriever import retrieve_context
from harness import mastery as mastery_model
from harness.context import GradingKey, StudentSnapshot
from harness.dialogue import DialogueOutcome, evaluate_reply
from harness.misconception import classify_misconception, classify_rules
from harness.problem_parser import parse_problem
from harness.question_generator import generate_transfer_question, pick_next_transfer
from harness.safety import check_output, screen_input
from harness.state import DONT_KNOW_LIMIT, MAX_TRANSFER_ATTEMPTS
from harness.text import is_dont_know
from harness.reference_solver import solve_reference
from harness.teaching_agent import build_feedback, teach
from harness.teaching_policy import select_strategy
from schemas.enums import MisconceptionType
from harness.verifier import verify_reasoning
from schemas.curriculum import Question, Topic
from schemas.harness import (
    AnalysisFeedback,
    CurriculumContext,
    Diagnosis,
    GeneratedQuestion,
    MasteryChange,
    QuestionQuality,
    SafetyReport,
    StrategyDecision,
    TeachingResponse,
    TraceStep,
    Verification,
)
from services.llm import LLMClient, LLMError
from services.prompts import render, system_user


class Tracer:
    def __init__(self):
        self.steps: list[TraceStep] = []

    @contextmanager
    def step(self, key: str, label: str):
        rec = TraceStep(key=key, step=label)
        t0 = time.perf_counter()
        try:
            yield rec
        except Exception:
            rec.status = "error"
            raise
        finally:
            rec.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            if rec.mode == "fallback" and rec.status == "complete":
                rec.status = "fallback"
            self.steps.append(rec)

    @property
    def total_ms(self) -> int:
        return max(1, round(sum(s.duration_ms for s in self.steps)))

    @property
    def mode(self) -> str:
        modes = {s.mode for s in self.steps}
        return "llm" if "llm" in modes else "fallback" if "fallback" in modes else "rules"


@dataclass
class BlockedResult:
    """The safety layer stopped grading (nothing is taught, no mastery change)."""

    safety: SafetyReport
    trace: Tracer


@dataclass
class InitialResult:
    context: CurriculumContext
    verification: Verification
    diagnosis: Diagnosis
    strategy: StrategyDecision
    teaching: TeachingResponse
    feedback: AnalysisFeedback
    transfer: GeneratedQuestion | None
    transfer_quality: QuestionQuality | None
    mastery: MasteryChange | None
    trace: Tracer
    safety: SafetyReport
    parsed_answer: str = ""
    missing_points: list[str] = field(default_factory=list)


@dataclass
class TransferResult:
    verification: Verification
    confirmed: bool
    feedback: str
    mastery: MasteryChange
    trace: Tracer
    safety: SafetyReport
    diagnosis: Diagnosis | None = None
    reteach: TeachingResponse | None = None
    next_question: GeneratedQuestion | None = None
    dont_know: bool = False  # this answer was a plain "I don't know"
    stuck: bool = False  # repeated "I don't know": end the question, flag the teacher


class PedagogicalHarness:
    def __init__(self, curriculum: Curriculum, llm: LLMClient):
        self.curriculum = curriculum
        self.llm = llm
        self.lr = get_settings().learning_rate

    # ------------------------------------------------------------------ helpers
    def _concept_name(self, topic: Topic, cid: str) -> str:
        c = topic.concept(cid)
        return c.name if c else cid

    # ------------------------------------------------------------------ initial answer
    def _screen(self, tr: Tracer, text: str, hint: str | None) -> SafetyReport:
        with tr.step("safety", "Safety & Privacy Check") as s:
            report = screen_input(text, hint)
            s.summary = report.category.value + (f" · redacted {', '.join(report.redactions)}" if report.redactions else "")
            s.output = report.model_dump(mode="json", exclude={"redacted_text"})
        return report

    async def run(
        self, topic: Topic, question: Question, student_answer: str, snapshot: StudentSnapshot, *, reassess: bool = False
    ) -> InitialResult | BlockedResult:
        """Full loop for a first answer. `reassess=True` re-diagnoses a clarified answer
        (no new transfer question, no mastery change)."""
        tr = Tracer()
        safety = self._screen(tr, student_answer, question.hints[0] if question.hints else None)
        if not safety.allow_grading:
            return BlockedResult(safety, tr)
        student_answer = safety.redacted_text

        with tr.step("curriculum", "Curriculum Retrieval") as s:
            ctx = retrieve_context(self.curriculum, topic, question)
            key = GradingKey.from_question(question, ctx.candidate_misconceptions)
            s.summary = f"{ctx.topic_name} › {ctx.concept_name}"
            s.output = {"concept": ctx.concept_id, "learning_objective": ctx.learning_objective, "candidate_misconceptions": ctx.candidate_misconceptions}

        with tr.step("parse", "Problem Parsing") as s:
            parsed = parse_problem(key, topic.topic_id, student_answer)
            s.step = "Student-Response Analysis"
            s.summary = (
                f"{parsed.word_count} words · "
                + ("explanation given" if parsed.has_explanation else "no explanation")
                + (f" · unsure ({', '.join(parsed.uncertainty_markers)})" if parsed.uncertain else "")
                + (" · looks like a guess" if parsed.is_blank_or_guess else "")
            )
            s.output = parsed.model_dump(exclude={"student_answer", "normalized_answer"}) | {"uncertain": parsed.uncertain}

        with tr.step("reference", "Reference Solution") as s:
            reference, s.mode = await solve_reference(self.llm, key, ctx)
            s.summary = f"{len(reference.reasoning_steps)} reasoning points, {len(reference.required_step_ids)} required"
            s.output = reference.model_dump()

        with tr.step("verify", "Reasoning Verification") as s:
            verification, s.mode = await verify_reasoning(self.llm, parsed, key, reference, ctx, topic, snapshot.age)
            s.summary = f"{verification.classification} · answer {'✓' if verification.answer_correct else '✗'} · reasoning {'✓' if verification.reasoning_correct else '✗'}"
            s.output = verification.model_dump(mode="json")

        with tr.step("diagnose", "Misconception Diagnosis") as s:
            diagnosis, s.mode = await classify_misconception(self.llm, verification, key, ctx, snapshot, topic)
            s.summary = diagnosis.label or "no gap"
            s.output = diagnosis.model_dump(mode="json")

        with tr.step("policy", "Teaching Strategy") as s:
            strategy = select_strategy(diagnosis, snapshot, ctx)
            s.summary = strategy.strategy.value.replace("_", " ").title()
            s.output = strategy.model_dump(mode="json")

        with tr.step("teach", "Teaching Response") as s:
            teaching, s.mode = await teach(self.llm, strategy, diagnosis, parsed, key, ctx, topic, snapshot)
            if teaching.strategy != strategy.strategy:
                strategy.reason += f" Using {teaching.strategy.value.replace('_', ' ').lower()} (authored content available)."
                strategy.strategy = teaching.strategy
            feedback = build_feedback(verification, diagnosis, key, topic, snapshot, parsed)
            s.summary = f"{len(teaching.messages)} messages" + (" + follow-up question" if teaching.follow_up else "")
            s.output = {"strategy": teaching.strategy.value, "messages": teaching.messages, "follow_up": teaching.follow_up}

        missing = [p for p in key.required_points if p not in verification.reasoning_points_hit]
        if reassess:
            return InitialResult(ctx, verification, diagnosis, strategy, teaching, feedback, None, None, None, tr, safety, student_answer, missing)

        with tr.step("transfer", "Transfer Question") as s:
            transfer, quality, s.mode, attempts = await generate_transfer_question(self.llm, question, key, diagnosis, ctx, topic, snapshot)
            s.summary = f"{transfer.source} · attempt {attempts}"
            s.output = {"id": transfer.id, "prompt": transfer.prompt, "source": transfer.source, "attempts": attempts}

        with tr.step("quality", "Question Quality Check") as s:
            s.summary = "approved" if quality.approved else "rejected → authored fallback"
            s.output = quality.model_dump(mode="json")

        with tr.step("mastery", "Mastery Update") as s:
            before = snapshot.mastery.get(question.concept, 0.0)
            evidence, reason = mastery_model.initial_evidence(verification, diagnosis)
            after = mastery_model.update(before, evidence, self.lr)
            change = MasteryChange(
                concept_id=question.concept, concept_name=self._concept_name(topic, question.concept), before=before, after=after, evidence=evidence, reason=reason
            )
            s.summary = f"{before:.2f} → {after:.2f} (evidence {evidence:+.1f})"
            s.output = change.model_dump()

        return InitialResult(ctx, verification, diagnosis, strategy, teaching, feedback, transfer, quality, change, tr, safety, student_answer, missing)

    # ------------------------------------------------------------------ dialogue
    def reply(
        self, topic: Topic, question: Question, reply: str, turn: int, misconception_id: str | None, strategy_used: str, missing_points: list[str]
    ) -> tuple[DialogueOutcome, Tracer]:
        tr = Tracer()
        ctx = retrieve_context(self.curriculum, topic, question)
        key = GradingKey.from_question(question, ctx.candidate_misconceptions)
        with tr.step("dialogue", "Dialogue Check") as s:
            outcome = evaluate_reply(reply, turn, key, topic, misconception_id, strategy_used, missing_points)
            s.summary = "idea repaired ✓" if outcome.resolved else ("moving on with key idea" if outcome.response.ready_for_transfer else "another angle")
            s.output = {"resolved": outcome.resolved, "misconception_reappeared": outcome.misconception_reappeared, "turn": turn, "strategy": outcome.response.strategy.value}
        return outcome, tr

    # ------------------------------------------------------------------ transfer answer
    async def run_transfer(
        self,
        topic: Topic,
        question: Question,
        transfer: GeneratedQuestion,
        answer: str,
        snapshot: StudentSnapshot,
        initial_misconception: str | None,
        attempt: int = 1,
        seen_ids: set[str] | None = None,
        dont_know_streak: int = 0,
    ) -> TransferResult | BlockedResult:
        """Score the question-back answer against the mastery criterion and pick the next
        state: advance, or (once) re-enter teaching with a second transfer question.
        `dont_know_streak` counts the student's consecutive "I don't know"s before this answer."""
        tr = Tracer()
        safety = self._screen(tr, answer, None)
        if not safety.allow_grading:
            return BlockedResult(safety, tr)
        answer = safety.redacted_text
        ctx = retrieve_context(self.curriculum, topic, question)
        if transfer.source == "teach_back":
            key = GradingKey.from_question(question, ctx.candidate_misconceptions)
            key.question_id, key.prompt = transfer.id, transfer.prompt
        elif transfer.source == "authored":
            tq = next(t for t in question.transfer_questions if t.id == transfer.authored_id)
            key = GradingKey.from_transfer(question, tq, ctx.candidate_misconceptions)
        else:
            key = GradingKey.from_generated(question, transfer, ctx.candidate_misconceptions)

        with tr.step("parse", "Problem Parsing") as s:
            parsed = parse_problem(key, topic.topic_id, answer)
            s.summary = f"{parsed.word_count} words"
            s.output = {"word_count": parsed.word_count}

        with tr.step("reference", "Reference Solution") as s:
            reference, s.mode = await solve_reference(self.llm, key, ctx)
            s.summary = transfer.source
            s.output = reference.model_dump()

        with tr.step("verify", "Transfer Verification") as s:
            v, s.mode = await verify_reasoning(self.llm, parsed, key, reference, ctx, topic, snapshot.age)
            s.summary = f"{v.classification} · answer {'✓' if v.answer_correct else '✗'} · reasoning {'✓' if v.reasoning_correct else '✗'}"
            s.output = v.model_dump(mode="json")

        confirmed = v.answer_correct and v.reasoning_correct
        repeated = any(m.id and m.id == initial_misconception for m in v.misconceptions)
        dont_know = is_dont_know(parsed.normalized_answer)
        stuck = dont_know and not confirmed and not v.misconceptions and dont_know_streak + 1 >= DONT_KNOW_LIMIT
        will_reteach = not confirmed and attempt < MAX_TRANSFER_ATTEMPTS and not stuck

        with tr.step("feedback", "Feedback") as s:
            if stuck:  # more questions would only frustrate: show the idea, hand over to the teacher
                feedback, s.mode = f"That's okay — this one is tricky. Here's how it works: {key.expected_answer} I've asked your teacher to go through it with you. 🤝", "rules"
            else:
                feedback, s.mode = await self._transfer_feedback(key, answer, v, confirmed, topic, ctx, reveal=not will_reteach)
            s.summary = "mastery confirmed" if confirmed else "stuck → teacher" if stuck else "not yet confirmed"
            s.output = {"feedback": feedback}

        with tr.step("mastery", "Mastery Verification") as s:
            before = snapshot.mastery.get(question.concept, 0.0)
            evidence, reason = mastery_model.transfer_evidence(v, repeated)
            after = mastery_model.update(before, evidence, self.lr)
            change = MasteryChange(
                concept_id=question.concept, concept_name=self._concept_name(topic, question.concept), before=before, after=after, evidence=evidence, reason=reason
            )
            s.summary = f"{before:.2f} → {after:.2f} (evidence {evidence:+.1f})"
            s.output = change.model_dump()

        result = TransferResult(v, confirmed, feedback, change, tr, safety, dont_know=dont_know, stuck=stuck)
        if will_reteach:
            # Re-enter the teaching/diagnostic cycle (proposal: mastery checker either
            # advances the student or re-enters teaching) — bounded to one extra attempt.
            with tr.step("reteach", "Re-teach & Next Question") as s:
                snap = StudentSnapshot(**{**snapshot.__dict__, "mastery": {**snapshot.mastery, question.concept: after}})
                diag = classify_rules(v, key, snap)
                if diag.classification == "unclear":
                    diag.type, diag.classification = MisconceptionType.MISSING_STEP, "incomplete"
                decision = select_strategy(diag, snap, ctx)
                parsed_t = parse_problem(key, topic.topic_id, answer)
                teaching, s.mode = await teach(self.llm, decision, diag, parsed_t, key, ctx, topic, snap)
                nxt = pick_next_transfer(question, {transfer.id, *(seen_ids or set())})
                result.diagnosis, result.reteach, result.next_question = diag, teaching, nxt
                s.summary = f"{decision.strategy.value.replace('_', ' ').title()} → {nxt.source} question"
                s.output = {"diagnosis": diag.model_dump(mode="json"), "strategy": teaching.strategy.value, "next_question": nxt.prompt}
        return result

    async def _transfer_feedback(self, key: GradingKey, answer: str, v: Verification, confirmed: bool, topic: Topic, ctx: CurriculumContext, reveal: bool = True):
        if not confirmed and not reveal:  # a second attempt is coming — don't give the answer away
            m = "fallback" if self.llm.available else "rules"
            if v.misconceptions:
                return f"Hmm — the old idea sneaked back in: “{v.misconceptions[0].statement}” Let's look at it once more.", m
            return "Not quite yet — let's look at it once more, then try another one. 💪", m
        if self.llm.available:
            try:
                from pydantic import BaseModel

                class _FB(BaseModel):
                    feedback: str

                prompt = render("transfer_feedback", question=key.prompt, student_answer=answer, verification=v.model_dump_json(), confirmed=confirmed)
                fb = await self.llm.generate(system_user(prompt), schema=_FB)
                if (problems := check_output(fb.feedback)):
                    raise LLMError("unsafe transfer feedback: " + ", ".join(problems))
                return fb.feedback, "llm"
            except LLMError:
                pass
        mode = "fallback" if self.llm.available else "rules"
        if confirmed:
            return f"Great — this time your explanation correctly uses the idea of **{ctx.concept_name.lower()}**. That's real understanding! 🎉", mode
        if v.misconceptions:
            return f"Careful — the old idea sneaked back in: “{v.misconceptions[0].statement}” Here's how a scientist would say it: {key.expected_answer}", mode
        if v.answer_correct:
            missing = [key.point_text[p] for p in key.required_points if p not in v.reasoning_points_hit]
            return f"Right answer! Next time add the *why*: {missing[0] if missing else key.expected_answer}", mode
        return f"Not quite yet — and that's okay. Here's the idea: {key.expected_answer}", mode
