"use client";

import { ArrowRight, CheckCircle2, XCircle } from "lucide-react";
import Link from "next/link";

import { Emoji } from "@/components/ui/emoji";
import { STRATEGY } from "@/lib/labels";
import { cn, timeAgo } from "@/lib/utils";
import type { TraceSummary } from "@/types/api";

export function TraceList({ traces }: { traces: TraceSummary[] }) {
  return (
    <ul className="divide-y divide-ink-100">
      {traces.map((t) => (
        <li key={t.id}>
          <Link href={`/teacher/trace/${t.id}`} className="group flex items-center gap-3 rounded-2xl px-2 py-3 transition hover:bg-curio-50/60">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-sun-50">
              <Emoji name={t.avatar} size={26} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 text-sm font-extrabold text-ink-900">
                {t.student_name}
                <span className="font-bold text-ink-400">· {t.concept_name}</span>
              </div>
              <div className="truncate text-xs font-semibold text-ink-500">“{t.answer}”</div>
              <div className="mt-1 flex flex-wrap gap-1.5">
                <Flag ok={!!t.answer_correct} label="Answer" />
                <Flag ok={!!t.reasoning_correct} label="Reasoning" />
                {t.misconception_label && <span className="rounded-full bg-coral-50 px-2 py-0.5 text-[10px] font-extrabold text-coral-700">{t.misconception_label}</span>}
                {t.strategy && <span className="rounded-full bg-curio-50 px-2 py-0.5 text-[10px] font-extrabold text-curio-700">{STRATEGY[t.strategy]?.label}</span>}
              </div>
            </div>
            <div className="hidden shrink-0 text-right sm:block">
              {t.mastery_before != null && t.mastery_after != null && (
                <div className={cn("text-sm font-black tabular-nums", t.mastery_after >= t.mastery_before ? "text-mint-600" : "text-coral-600")}>
                  {Math.round(t.mastery_before * 100)}→{Math.round(t.mastery_after * 100)}%
                </div>
              )}
              <div className="text-[11px] font-bold text-ink-400">{timeAgo(t.created_at)}</div>
            </div>
            <ArrowRight className="h-4 w-4 shrink-0 text-ink-300 transition group-hover:translate-x-1 group-hover:text-curio-500" />
          </Link>
        </li>
      ))}
    </ul>
  );
}

function Flag({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={cn("inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[10px] font-extrabold", ok ? "bg-mint-50 text-mint-700" : "bg-ink-100 text-ink-500")}>
      {ok ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
      {label}
    </span>
  );
}
