"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, CheckCircle2, Cpu, ShieldAlert, XCircle, Zap } from "lucide-react";
import Link from "next/link";
import { use, useMemo, useState } from "react";

import { CurioBubble, StudentBubble } from "@/components/learn/chat";
import { LearningStateCard } from "@/components/learn/learning-state";
import { TracePipeline, type PipelineNode } from "@/components/teacher/trace-pipeline";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Emoji } from "@/components/ui/emoji";
import { Skeleton } from "@/components/ui/skeleton";
import { useTrace } from "@/lib/hooks";
import { CLASSIFICATION, MISCONCEPTION_TYPE, MODE_LABEL, STRATEGY } from "@/lib/labels";
import { cn, fmtMs, timeAgo } from "@/lib/utils";
import type { TraceDetail, TraceStep } from "@/types/api";

const yes = (ok: boolean | null | undefined) =>
  ok ? (
    <span className="inline-flex items-center gap-1 text-mint-600">
      <CheckCircle2 className="h-4 w-4" /> YES
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-coral-600">
      <XCircle className="h-4 w-4" /> NO
    </span>
  );

function buildNodes(t: TraceDetail): PipelineNode[] {
  const v = t.verification;
  const nodes: PipelineNode[] = [
    { key: "answer", title: "Student answer", emoji: <Emoji name={t.avatar} size={24} />, value: <span className="font-bold italic">“{t.answer}”</span>, tone: "neutral", stepKeys: ["i:safety", "i:curriculum", "i:parse"] },
    { key: "answer_ok", title: "Answer correct", emoji: <Emoji name="direct_hit" size={22} />, value: yes(t.answer_correct), tone: t.answer_correct ? "good" : "bad", stepKeys: ["i:reference", "i:verify"] },
    {
      key: "reasoning_ok",
      title: "Reasoning correct",
      emoji: <Emoji name="brain" size={22} />,
      value: (
        <span className="flex flex-wrap items-center gap-2">
          {yes(t.reasoning_correct)}
          {v.classification && <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-extrabold", CLASSIFICATION[v.classification].tone)}>{CLASSIFICATION[v.classification].label}</span>}
          <span className="text-xs font-bold text-ink-500">{v.reasoning_summary}</span>
        </span>
      ),
      tone: t.reasoning_correct ? "good" : "bad",
      stepKeys: ["i:verify"],
    },
  ];
  if (t.misconception_label || t.diagnosis?.type) {
    nodes.push({
      key: "misconception",
      title: "Misconception",
      emoji: <Emoji name="warning" size={22} />,
      value: (
        <span>
          {t.misconception_label}
          {t.diagnosis?.type && <span className="ml-2 rounded-full bg-white px-2 py-0.5 text-[11px] font-extrabold text-coral-700 ring-1 ring-coral-200">{MISCONCEPTION_TYPE[t.diagnosis.type]}</span>}
          {t.diagnosis?.student_claim && <div className="mt-1 text-xs font-bold italic text-ink-500">claim: “{t.diagnosis.student_claim}”</div>}
        </span>
      ),
      tone: "warn",
      stepKeys: ["i:diagnose"],
    });
  }
  if (t.strategy) {
    nodes.push({
      key: "strategy",
      title: "Teaching strategy",
      emoji: <Emoji name="light_bulb" size={22} />,
      value: (
        <span>
          {STRATEGY[t.strategy]?.label}
          {t.teaching?.reason && <div className="mt-0.5 text-xs font-bold text-ink-500">{t.teaching.reason}</div>}
        </span>
      ),
      tone: "brand",
      stepKeys: ["i:policy", "i:teach"],
    });
  }
  if (t.transfer_question) {
    nodes.push({
      key: "transfer",
      title: `Transfer question · ${t.transfer_question.source}`,
      emoji: <Emoji name="rocket" size={22} />,
      value: <span className="text-sm">{t.transfer_question.prompt}</span>,
      tone: "sky",
      stepKeys: ["i:transfer", "i:quality"],
    });
  }
  if (t.transfer_answer) {
    nodes.push({
      key: "transfer_answer",
      title: "Transfer answer",
      emoji: <Emoji name="speech_balloon" size={22} />,
      value: (
        <span>
          <span className="font-bold italic">“{t.transfer_answer}”</span>
          <div className="mt-1">{yes(t.transfer_confirmed)} <span className="text-xs text-ink-500">understanding verified in a new context</span></div>
        </span>
      ),
      tone: t.transfer_confirmed ? "good" : "warn",
      stepKeys: ["t:parse", "t:verify", "t:feedback"],
    });
  }
  const before = t.mastery_before ?? 0;
  const after = t.final_mastery ?? t.mastery_after ?? before;
  nodes.push({
    key: "mastery",
    title: `Mastery · ${t.concept_name}`,
    emoji: <Emoji name="chart_increasing" size={22} />,
    value: (
      <span className="text-2xl font-black tabular-nums">
        {before.toFixed(2)} →{" "}
        <span className={after >= before ? "text-mint-600" : "text-coral-600"}>
          <AnimatedNumber value={after} from={before} format={(n) => n.toFixed(2)} delay={1} duration={1.4} />
        </span>
      </span>
    ),
    tone: after > before ? "good" : "neutral",
    stepKeys: ["i:mastery", "t:mastery"],
  });
  return nodes;
}

export default function TracePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: t, isLoading } = useTrace(id);
  const nodes = useMemo(() => (t ? buildNodes(t) : []), [t]);
  const [active, setActive] = useState<string>("misconception");
  const activeNode = nodes.find((n) => n.key === active) ?? nodes[0];

  if (isLoading || !t) {
    return (
      <div className="mx-auto max-w-7xl space-y-4 px-4 py-8 sm:px-8">
        <Skeleton className="h-24" />
        <Skeleton className="h-[600px]" />
      </div>
    );
  }

  const allSteps: (TraceStep & { ref: string; phase: string })[] = [
    ...t.steps.map((s) => ({ ...s, ref: `i:${s.key}`, phase: "Answer" })),
    ...t.transfer_steps.map((s) => ({ ...s, ref: `t:${s.key}`, phase: "Transfer" })),
  ];
  const maxMs = Math.max(1, ...allSteps.map((s) => s.duration_ms));
  const focused = allSteps.filter((s) => activeNode?.stepKeys?.includes(s.ref));

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-8">
      <Button asChild variant="ghost" size="sm" className="mb-3">
        <Link href="/teacher">
          <ArrowLeft /> Class insights
        </Link>
      </Button>

      <Card className="relative overflow-hidden p-6">
        <div className="absolute -right-10 -top-16 h-48 w-48 rounded-full bg-curio-100 blur-2xl" />
        <div className="relative flex flex-wrap items-start gap-4">
          <div className="grid h-16 w-16 place-items-center rounded-3xl bg-sun-50">
            <Emoji name={t.avatar} size={44} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="label-caps">AI diagnosis trace</div>
            <h1 className="text-2xl font-black text-ink-900">
              {t.student_name} · {t.concept_name}
            </h1>
            <p className="mt-1 max-w-3xl text-[15px] font-bold text-ink-600">{t.question_prompt}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">{timeAgo(t.created_at)}</Badge>
            <Badge variant={t.mode === "llm" ? "sky" : "ink"}>
              {t.mode === "llm" ? <Zap /> : <Cpu />} {MODE_LABEL[t.mode] ?? t.mode}
            </Badge>
            <Badge variant="default">{allSteps.length} harness steps</Badge>
          </div>
        </div>
      </Card>

      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
        <Card className="p-5">
          <div className="label-caps mb-3">Decision pipeline — click a step to inspect</div>
          <TracePipeline nodes={nodes} active={activeNode?.key} onSelect={(n) => setActive(n.key)} />
        </Card>

        <div className="space-y-5">
          <Card className="p-5">
            <div className="label-caps mb-2">Inspecting</div>
            <AnimatePresence mode="wait">
              <motion.div key={activeNode?.key} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <h2 className="mb-3 text-xl font-black text-ink-900">{activeNode?.title}</h2>
                {focused.length === 0 && <p className="text-sm font-bold text-ink-400">No harness step recorded for this node.</p>}
                <div className="space-y-3">
                  {focused.map((s) => (
                    <StepCard key={s.ref} s={s} phase={s.phase} />
                  ))}
                </div>
              </motion.div>
            </AnimatePresence>
          </Card>

          {t.learning_state && (
            <Card className="p-5">
              <div className="label-caps mb-3">Learning state · explicit transitions</div>
              <LearningStateCard state={t.learning_state} />
            </Card>
          )}

          {t.transfer_attempts.length > 1 && (
            <Card className="p-5">
              <div className="label-caps mb-3">Question-back attempts (re-teach loop)</div>
              <ol className="space-y-2">
                {t.transfer_attempts.map((a) => (
                  <li key={a.attempt} className={cn("rounded-2xl p-3 text-sm", a.confirmed ? "bg-mint-50" : "bg-sun-50")}>
                    <div className="text-xs font-extrabold text-ink-500">
                      Attempt {a.attempt} · {a.source} · {a.confirmed ? "verified ✓" : "not yet"}
                    </div>
                    <div className="font-bold text-ink-800">{a.prompt}</div>
                    <div className="mt-1 italic text-ink-600">“{a.answer}”</div>
                  </li>
                ))}
              </ol>
            </Card>
          )}

          <Card className="p-5">
            <div className="label-caps mb-3">Harness timeline</div>
            <ul className="space-y-1.5">
              {allSteps.map((s) => {
                const node = nodes.find((n) => n.stepKeys?.includes(s.ref));
                return (
                  <li key={s.ref}>
                    <button onClick={() => node && setActive(node.key)} className={cn("grid w-full grid-cols-[150px_1fr_56px] items-center gap-3 rounded-xl px-2 py-1 text-left hover:bg-ink-50", activeNode?.stepKeys?.includes(s.ref) && "bg-curio-50")}>
                      <span className="truncate text-xs font-extrabold text-ink-700">
                        <span className="text-ink-400">{s.phase === "Transfer" ? "T · " : ""}</span>
                        {s.step}
                      </span>
                      <span className="h-2.5 overflow-hidden rounded-full bg-ink-100">
                        <motion.span
                          className={cn("block h-full rounded-full", s.status === "fallback" ? "bg-sun-400" : s.mode === "llm" ? "bg-sky-500" : "bg-curio-400")}
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.max(4, (s.duration_ms / maxMs) * 100)}%` }}
                        />
                      </span>
                      <span className="text-right text-[11px] font-bold tabular-nums text-ink-400">{fmtMs(s.duration_ms)}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
            <div className="mt-3 flex gap-3 text-[11px] font-bold text-ink-400">
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-curio-400" /> Curriculum rules</span>
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-sky-500" /> LLM</span>
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-sun-400" /> Safe fallback</span>
            </div>
          </Card>

          <Card className="p-5">
            <div className="label-caps mb-3">Teaching conversation</div>
            <div className="scroll-thin max-h-[420px] space-y-3 overflow-y-auto pr-1">
              {t.dialogue.map((d, i) => (d.role === "curio" ? <CurioBubble key={i} text={d.text} showAvatar={t.dialogue[i + 1]?.role !== "curio"} /> : <StudentBubble key={i} text={d.text} avatar={t.avatar} />))}
              {t.transfer_feedback && <CurioBubble text={t.transfer_feedback} mood={t.transfer_confirmed ? "happy" : "curious"} />}
            </div>
            <p className="mt-3 flex items-center gap-1.5 text-[11px] font-bold text-ink-400">
              <ShieldAlert className="h-3.5 w-3.5" /> Raw model prompts are never shown or stored — only structured step outputs.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}

function StepCard({ s, phase }: { s: TraceStep; phase: string }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-ink-200">
      <div className="flex flex-wrap items-center justify-between gap-2 bg-ink-50 px-3.5 py-2">
        <span className="text-sm font-extrabold text-ink-800">
          {phase === "Transfer" && <span className="text-ink-400">Transfer · </span>}
          {s.step}
        </span>
        <span className="flex items-center gap-1.5">
          <Badge variant={s.status === "fallback" ? "sun" : "mint"}>{s.status}</Badge>
          <Badge variant={s.mode === "llm" ? "sky" : "ink"}>{MODE_LABEL[s.mode]}</Badge>
          <Badge variant="outline">{fmtMs(s.duration_ms)}</Badge>
        </span>
      </div>
      <div className="px-3.5 py-2 text-sm font-bold text-ink-600">{s.summary}</div>
      <pre className="scroll-thin max-h-72 overflow-auto bg-ink-900 px-3.5 py-3 font-mono text-[11.5px] leading-relaxed text-curio-100">{JSON.stringify(s.output, null, 2)}</pre>
    </div>
  );
}
