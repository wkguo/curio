"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, ArrowRight, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { mutate } from "swr";

import { AnalysisPanel } from "@/components/learn/analysis-panel";
import { AnswerBox } from "@/components/learn/answer-box";
import { CurioBubble, StudentBubble, TypingBubble } from "@/components/learn/chat";
import { HeatFlowVisual } from "@/components/learn/heat-flow-visual";
import { SafetyBubble } from "@/components/learn/safety-bubble";
import { MasteryResult } from "@/components/learn/mastery-result";
import { QuestionCard } from "@/components/learn/question-card";
import { RightPanel } from "@/components/learn/right-panel";
import { StrategyChip } from "@/components/learn/strategy-chip";
import { SUBMIT_STEPS, ThinkingSteps, TRANSFER_STEPS } from "@/components/learn/thinking-steps";
import { TransferCard } from "@/components/learn/transfer-card";
import { Curio } from "@/components/mascot/curio";
import { Button } from "@/components/ui/button";
import { Confetti } from "@/components/ui/confetti";
import { Emoji } from "@/components/ui/emoji";
import { Skeleton } from "@/components/ui/skeleton";
import { api, CurioError, FRIENDLY_ERROR } from "@/lib/api";
import { useStudents, useTopic } from "@/lib/hooks";
import { useStudent } from "@/lib/student-context";
import { cn, sleep } from "@/lib/utils";
import type {
  AnalysisFeedback,
  LearningState,
  PublicQuestion,
  QuestionQuality,
  SafetyNotice,
  Session,
  SubmitResponse,
  TeachingResponse,
  TeachingStrategy,
  TransferResponse,
  Verification,
} from "@/types/api";

type Item =
  | { id: string; kind: "student"; text: string }
  | { id: string; kind: "thinking"; variant: "submit" | "transfer" }
  | { id: string; kind: "analysis"; feedback: AnalysisFeedback; verification?: Verification | null }
  | { id: string; kind: "strategy"; strategy: TeachingStrategy; reason?: string }
  | { id: string; kind: "curio"; text: string; highlight?: boolean }
  | { id: string; kind: "visual"; visual: string }
  | { id: string; kind: "typing" }
  | { id: string; kind: "transfer"; q: PublicQuestion; quality?: QuestionQuality | null }
  | { id: string; kind: "result"; result: TransferResponse }
  | { id: string; kind: "notice"; category: SafetyNotice["category"]; text: string }
  | { id: string; kind: "deferred" }
  | { id: string; kind: "error"; text: string };

type Phase = "answer" | "thinking" | "teaching" | "ready" | "transfer" | "verifying" | "result" | "deferred";

let seq = 0;
const uid = () => `i${++seq}`;

export function LearningSession({ topicId, onExit }: { topicId: string; onExit: () => void }) {
  const { studentId } = useStudent();
  const { data: students } = useStudents();
  const avatar = students?.find((s) => s.id === studentId)?.avatar ?? "fox";
  const isDemo = students?.find((s) => s.id === studentId)?.is_demo ?? true;
  const { data: topic } = useTopic(topicId);

  const [session, setSession] = useState<Session | null>(null);
  const [index, setIndex] = useState(0);
  const [items, setItems] = useState<Item[]>([]);
  const [phase, setPhase] = useState<Phase>("answer");
  const [answer, setAnswer] = useState("");
  const [reply, setReply] = useState("");
  const [transferAnswer, setTransferAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [sub, setSub] = useState<SubmitResponse | null>(null);
  const [pendingSubmit, setPendingSubmit] = useState<SubmitResponse | null>(null);
  const [pendingTransfer, setPendingTransfer] = useState<TransferResponse | null>(null);
  const [previous, setPrevious] = useState<Record<string, number>>({});
  const [results, setResults] = useState<TransferResponse[]>([]);
  const [learnState, setLearnState] = useState<LearningState | null>(null);
  const [transferDemo, setTransferDemo] = useState("");
  const [activeTransferId, setActiveTransferId] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const alive = useRef(true);
  const endRef = useRef<HTMLDivElement>(null);
  const started = useRef(false);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    api.startSession(studentId, topicId, 5).then(setSession).catch(() => setSession(null));
  }, [studentId, topicId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [items.length, phase]);

  const q = session?.questions[index];
  const color = session?.topic_color ?? topic?.color ?? "#7C5CFF";

  const push = (...it: Item[]) => setItems((xs) => [...xs, ...it]);
  const replace = (id: string, it: Item | null) => setItems((xs) => (it ? xs.map((x) => (x.id === id ? it : x)) : xs.filter((x) => x.id !== id)));

  const refreshMastery = useCallback(
    (conceptId: string, before: number) => {
      setPrevious((p) => ({ ...p, [conceptId]: before }));
      mutate((key) => Array.isArray(key) && ["topic", "dashboard", "mastery", "topics"].includes(key[0]));
    },
    [],
  );

  /** Reveal Curio's teaching bubbles one by one with a typing indicator. */
  const playTeaching = useCallback(async (t: TeachingResponse, opts: { chip?: boolean; reason?: string; thenPhase?: Phase } = {}) => {
    if (opts.chip) push({ id: uid(), kind: "strategy", strategy: t.strategy, reason: opts.reason });
    const all = [...t.messages];
    for (let k = 0; k < all.length; k++) {
      const typing = { id: uid(), kind: "typing" as const };
      push(typing);
      await sleep(Math.min(1300, 450 + all[k].length * 9));
      if (!alive.current) return;
      replace(typing.id, { id: uid(), kind: "curio", text: all[k] });
      if (k === 0 && t.visual) push({ id: uid(), kind: "visual", visual: t.visual });
    }
    if (t.follow_up) {
      const typing = { id: uid(), kind: "typing" as const };
      push(typing);
      await sleep(700);
      if (!alive.current) return;
      replace(typing.id, { id: uid(), kind: "curio", text: t.follow_up, highlight: !opts.thenPhase });
    }
    setPhase(opts.thenPhase ?? (t.ready_for_transfer ? "ready" : "teaching"));
  }, []);

  const pushNotice = (n: SafetyNotice) => push({ id: uid(), kind: "notice", category: n.category, text: n.message });

  // ---------------------------------------------------------------- actions
  const submitAnswer = async () => {
    if (!q) return;
    const thinking = { id: uid(), kind: "thinking" as const, variant: "submit" as const };
    push({ id: uid(), kind: "student", text: answer.trim() }, thinking);
    setPhase("thinking");
    setBusy(true);
    try {
      const r = await api.submit(studentId, q.id, answer.trim(), session?.session_id);
      setPendingSubmit(r);
    } catch (e) {
      replace(thinking.id, { id: uid(), kind: "error", text: e instanceof CurioError ? e.message : FRIENDLY_ERROR });
      setPhase("answer");
    } finally {
      setBusy(false);
    }
  };

  const onSubmitThinkingDone = useCallback(
    async (thinkingId: string) => {
      const r = pendingSubmit;
      if (!r) return;
      setPendingSubmit(null);
      if (r.blocked || !r.feedback || !r.teaching_response) {
        // safety layer: not graded, nothing taught — show the message and let the student try again
        replace(thinkingId, null);
        if (r.safety) pushNotice(r.safety);
        setAnswer("");
        setPhase("answer");
        return;
      }
      setSub(r);
      setLearnState(r.learning_state);
      replace(thinkingId, { id: uid(), kind: "analysis", feedback: r.feedback, verification: r.verification });
      if (r.safety) pushNotice(r.safety);
      if (r.mastery_change && r.mastery_before != null) refreshMastery(r.mastery_change.concept_id, r.mastery_before);
      await sleep(900);
      await playTeaching(r.teaching_response, { chip: true, reason: r.strategy_reason });
    },
    [pendingSubmit, playTeaching, refreshMastery],
  );

  const sendReply = async () => {
    if (!sub?.interaction_id) return;
    const text = reply.trim();
    setReply("");
    push({ id: uid(), kind: "student", text });
    setBusy(true);
    try {
      const r = await api.reply(studentId, sub.interaction_id, text);
      if (r.blocked) {
        if (r.safety) pushNotice(r.safety);
        return;
      }
      if (r.safety) pushNotice(r.safety);
      setLearnState(r.learning_state);
      if (r.analysis) {
        // the clarified answer was re-assessed: show the new verdict first
        push({ id: uid(), kind: "analysis", feedback: r.analysis });
        await sleep(700);
      }
      const changed = (r.teaching_response.strategy !== sub.teaching_strategy && !r.resolved) || !!r.analysis;
      if (r.analysis) setSub({ ...sub, teaching_strategy: r.teaching_response.strategy });
      if (r.deferred) {
        await playTeaching(r.teaching_response, { chip: false, thenPhase: "deferred" });
        push({ id: uid(), kind: "deferred" });
        return;
      }
      await playTeaching({ ...r.teaching_response, ready_for_transfer: r.ready_for_transfer }, { chip: changed });
    } catch (e) {
      push({ id: uid(), kind: "error", text: e instanceof CurioError ? e.message : FRIENDLY_ERROR });
    } finally {
      setBusy(false);
    }
  };

  const startTransfer = () => {
    if (!sub?.transfer_question) return;
    const id = uid();
    push({ id, kind: "transfer", q: sub.transfer_question, quality: sub.question_quality });
    setActiveTransferId(id);
    setTransferDemo(sub.transfer_demo_answer);
    setPhase("transfer");
  };

  const submitTransfer = async () => {
    if (!sub?.interaction_id) return;
    const text = transferAnswer.trim();
    const thinking = { id: uid(), kind: "thinking" as const, variant: "transfer" as const };
    push({ id: uid(), kind: "student", text }, thinking);
    setTransferAnswer("");
    setPhase("verifying");
    setBusy(true);
    try {
      const r = await api.transfer(studentId, sub.interaction_id, text);
      setPendingTransfer(r);
    } catch (e) {
      replace(thinking.id, { id: uid(), kind: "error", text: e instanceof CurioError ? e.message : FRIENDLY_ERROR });
      setPhase("transfer");
    } finally {
      setBusy(false);
    }
  };

  const onTransferThinkingDone = useCallback(
    async (thinkingId: string) => {
      const r = pendingTransfer;
      if (!r) return;
      setPendingTransfer(null);
      if (r.blocked) {
        replace(thinkingId, null);
        if (r.safety) pushNotice(r.safety);
        setPhase("transfer");
        return;
      }
      setLearnState(r.learning_state);
      replace(thinkingId, { id: uid(), kind: "result", result: r });
      if (r.mastery_change && r.mastery_before != null) refreshMastery(r.mastery_change.concept_id, r.mastery_before);
      if (r.next_state === "reteach" && r.next_transfer_question) {
        // re-enter the teaching cycle, then ask a second question back
        setPhase("verifying");
        await sleep(700);
        if (r.teaching_response) await playTeaching(r.teaching_response, { chip: true, thenPhase: "verifying" });
        const id = uid();
        push({ id, kind: "transfer", q: r.next_transfer_question });
        setActiveTransferId(id);
        setTransferDemo(r.next_transfer_demo_answer);
        setPhase("transfer");
        return;
      }
      setResults((xs) => [...xs, r]);
      setPhase("result");
    },
    [pendingTransfer, refreshMastery, playTeaching],
  );

  const next = () => {
    if (!session) return;
    if (index + 1 >= session.questions.length) {
      setDone(true);
      return;
    }
    setIndex((i) => i + 1);
    setItems([]);
    setAnswer("");
    setReply("");
    setTransferAnswer("");
    setSub(null);
    setLearnState(null);
    setActiveTransferId(null);
    setTransferDemo("");
    setPhase("answer");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // ---------------------------------------------------------------- render
  if (!session || !q) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-8">
        <Skeleton className="mb-4 h-10 w-64" />
        <Skeleton className="h-44" />
      </div>
    );
  }

  if (done) return <SessionComplete results={results} topicName={session.topic_name} onRestart={onExit} />;

  const demoInitial = isDemo
    ? [
        q.demo_answers.misconception && { label: "🤔 Alex's answer", text: q.demo_answers.misconception },
        q.demo_answers.correct && { label: "✅ Strong answer", text: q.demo_answers.correct },
      ].filter(Boolean)
    : [];

  return (
    <div className="mx-auto grid max-w-[1320px] gap-6 px-4 py-6 sm:px-8 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div className="min-w-0">
        {/* Header */}
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Button variant="secondary" size="icon" onClick={onExit} aria-label="Back to topics">
              <ArrowLeft />
            </Button>
            <div>
              <div className="flex items-center gap-2 text-xl font-black text-ink-900">
                {topic && <Emoji name={topic.emoji} size={26} />}
                {session.topic_name}
              </div>
              <div className="text-sm font-bold text-ink-400">
                Question {index + 1} / {session.total}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1.5" aria-label="Session progress">
            {session.questions.map((qq, k) => (
              <motion.span
                key={qq.id}
                layout
                className={cn("h-2.5 rounded-full", k < index ? "w-6" : k === index ? "w-10" : "w-2.5 bg-ink-200")}
                style={k <= index ? { background: k < index ? "#1FB978" : color } : undefined}
              />
            ))}
          </div>
        </div>

        <QuestionCard key={q.id} q={q} color={color} compact={phase !== "answer"} />

        {/* Conversation */}
        <div className="mt-5 space-y-4">
          <AnimatePresence initial={false}>
            {items.map((it) => (
              <motion.div key={it.id} layout="position">
                {it.kind === "student" && <StudentBubble text={it.text} avatar={avatar} />}
                {it.kind === "typing" && <TypingBubble />}
                {it.kind === "curio" && <CurioBubble text={it.text} highlight={it.highlight} />}
                {it.kind === "strategy" && <StrategyChip strategy={it.strategy} reason={it.reason} />}
                {it.kind === "visual" && it.visual === "heat_flow_hand" && <HeatFlowVisual />}
                {it.kind === "analysis" && <AnalysisPanel feedback={it.feedback} verification={it.verification} />}
                {it.kind === "thinking" && (
                  <ThinkingSteps
                    steps={it.variant === "submit" ? SUBMIT_STEPS : TRANSFER_STEPS}
                    ready={it.variant === "submit" ? !!pendingSubmit : !!pendingTransfer}
                    onDone={() => (it.variant === "submit" ? onSubmitThinkingDone(it.id) : onTransferThinkingDone(it.id))}
                    pace={it.variant === "submit" ? 480 : 520}
                  />
                )}
                {it.kind === "transfer" && (
                  <TransferCard q={it.q} quality={it.quality ?? undefined}>
                    {phase === "transfer" && it.id === activeTransferId && (
                      <AnswerBox
                        value={transferAnswer}
                        onChange={setTransferAnswer}
                        onSubmit={submitTransfer}
                        busy={busy}
                        placeholder="Explain your answer — what happens, and why?"
                        cta="Check my understanding"
                        variant="mint"
                        demo={isDemo && transferDemo ? [{ label: "✨ Alex's answer", text: transferDemo }] : []}
                      />
                    )}
                  </TransferCard>
                )}
                {it.kind === "result" && <MasteryResult result={it.result} onNext={next} isLast={index + 1 >= session.questions.length} />}
                {it.kind === "notice" && <SafetyBubble category={it.category} text={it.text} />}
                {it.kind === "deferred" && (
                  <div className="flex flex-wrap items-center justify-between gap-3 rounded-3xl border-2 border-sky-200 bg-sky-50 p-4">
                    <div className="flex items-center gap-3">
                      <Emoji name="teacher" size={40} />
                      <div>
                        <div className="text-sm font-black text-ink-900">Sent to your teacher</div>
                        <div className="text-xs font-bold text-ink-500">Curio wasn&apos;t sure enough to teach this safely, so a human will check it.</div>
                      </div>
                    </div>
                    <Button onClick={next}>
                      {index + 1 >= session.questions.length ? "Finish session" : "Next question"} <ArrowRight />
                    </Button>
                  </div>
                )}
                {it.kind === "error" && (
                  <div className="flex items-center gap-3 rounded-3xl border-2 border-sun-200 bg-sun-50 p-4">
                    <Curio size={48} mood="curious" />
                    <p className="text-[15px] font-bold text-ink-700">{it.text}</p>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Inputs */}
        <div className="mt-5">
          {phase === "answer" && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="card-base p-4 sm:p-5">
              <AnswerBox
                value={answer}
                onChange={setAnswer}
                onSubmit={submitAnswer}
                busy={busy}
                placeholder="Type your answer AND explain why… (e.g. “I think… because…”)"
                cta="Submit Answer"
                demo={demoInitial as { label: string; text: string }[]}
                rows={4}
              />
            </motion.div>
          )}
          {phase === "teaching" && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="card-base p-4">
              <AnswerBox
                value={reply}
                onChange={setReply}
                onSubmit={sendReply}
                busy={busy}
                placeholder="Share your thinking with Curio…"
                cta="Reply"
                rows={2}
                demo={isDemo && q.demo_answers.dialogue ? [{ label: "💡 Alex's idea", text: q.demo_answers.dialogue }] : []}
              />
            </motion.div>
          )}
          {phase === "ready" && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="flex justify-center">
              <Button size="xl" variant="sun" onClick={startTransfer}>
                <Emoji name="rocket" size={26} /> Take the transfer challenge
              </Button>
            </motion.div>
          )}
        </div>
        <div ref={endRef} className="h-4" />
      </div>

      <aside className="hidden xl:block">
        <div className="sticky top-6">
          <RightPanel
            concepts={topic?.concepts}
            currentConcept={q.concept_id}
            previous={previous}
            strategy={sub?.teaching_strategy ?? undefined}
            strategyReason={sub?.strategy_reason}
            learningState={learnState}
            trace={sub?.trace}
            traceId={sub?.trace_id}
          />
        </div>
      </aside>
    </div>
  );
}

function SessionComplete({ results, topicName, onRestart }: { results: TransferResponse[]; topicName: string; onRestart: () => void }) {
  const confirmed = results.filter((r) => r.mastery_confirmed).length;
  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card-base relative overflow-hidden p-8 text-center">
        <Confetti pieces={90} />
        <div className="relative">
          <Curio size={130} mood="celebrate" className="mx-auto" />
          <h1 className="mt-4 text-3xl font-black text-ink-900">Session complete!</h1>
          <p className="mt-2 text-[15px] font-bold text-ink-500">
            {topicName} · you verified your understanding {confirmed} of {results.length} times.
          </p>
          <ul className="mt-6 space-y-2 text-left">
            {results
              .filter((r) => r.mastery_change)
              .map((r) => (
                <li key={r.interaction_id} className="flex items-center gap-3 rounded-2xl bg-ink-50 px-4 py-3">
                  <Emoji name={r.mastery_confirmed ? "check_mark_button" : "seedling"} size={24} />
                  <span className="flex-1 font-extrabold text-ink-800">{r.mastery_change!.concept_name}</span>
                  <span className="font-black tabular-nums text-mint-600">
                    {Math.round(r.mastery_change!.before * 100)}% → {Math.round(r.mastery_change!.after * 100)}%
                  </span>
                </li>
              ))}
          </ul>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button asChild size="lg">
              <Link href="/progress">
                See my progress <ArrowRight />
              </Link>
            </Button>
            <Button variant="secondary" size="lg" onClick={onRestart}>
              <RotateCcw /> Another topic
            </Button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
