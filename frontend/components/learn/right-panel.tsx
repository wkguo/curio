"use client";

import { ChevronDown, Cpu, ExternalLink, Zap } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { LearningStateCard } from "@/components/learn/learning-state";
import { Curio } from "@/components/mascot/curio";
import { ConceptBar } from "@/components/shared/concept-bar";
import { RichText } from "@/components/ui/rich-text";
import { Skeleton } from "@/components/ui/skeleton";
import { STRATEGY } from "@/lib/labels";
import { cn, fmtMs } from "@/lib/utils";
import type { ConceptNode, LearningState, TeachingStrategy, TraceStep } from "@/types/api";

export function RightPanel({
  concepts,
  currentConcept,
  previous,
  strategy,
  strategyReason,
  trace,
  traceId,
  learningState,
}: {
  concepts?: ConceptNode[];
  currentConcept?: string;
  previous: Record<string, number>;
  strategy?: TeachingStrategy;
  strategyReason?: string;
  trace?: TraceStep[];
  traceId?: string;
  learningState?: LearningState | null;
}) {
  const [open, setOpen] = useState(true);
  return (
    <div className="space-y-4">
      <div className="card-base p-4">
        <div className="label-caps mb-2 px-1">Concept mastery</div>
        {!concepts ? (
          <div className="space-y-2">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : (
          <div className="space-y-1">
            {concepts.map((c) => (
              <ConceptBar key={c.id} concept={c} highlight={c.id === currentConcept} from={previous[c.id]} />
            ))}
          </div>
        )}
      </div>

      {learningState && (
        <div className="card-base p-4">
          <div className="label-caps mb-2">Learning state</div>
          <LearningStateCard state={learningState} />
        </div>
      )}

      <div className="card-base overflow-hidden">
        <div className="flex items-center gap-3 bg-curio-50 px-4 py-3">
          <Curio size={38} mood="curious" />
          <div className="label-caps !text-curio-600">Curio insight</div>
        </div>
        <div className="p-4 text-sm font-bold leading-relaxed text-ink-600">
          {strategy ? (
            <>
              <div className="mb-1 text-ink-900">
                Why a <span className="text-curio-600">{STRATEGY[strategy].label.toLowerCase()}</span>?
              </div>
              <RichText text={strategyReason || STRATEGY[strategy].blurb} />
            </>
          ) : (
            <>A correct answer is a great start — but Curio checks <b className="text-ink-900">why</b> it&apos;s correct, then asks a new question to make sure the idea really stuck.</>
          )}
        </div>
      </div>

      {trace && trace.length > 0 && (
        <div className="card-base overflow-hidden">
          <button onClick={() => setOpen((o) => !o)} className="flex w-full items-center justify-between px-4 py-3">
            <span className="label-caps">Behind the scenes</span>
            <ChevronDown className={cn("h-4 w-4 text-ink-400 transition", open && "rotate-180")} />
          </button>
          {open && (
            <div className="px-4 pb-4">
              <ol className="relative space-y-2 border-l-2 border-dashed border-ink-200 pl-4">
                {trace.map((s) => (
                  <li key={s.key} className="relative">
                    <span className={cn("absolute -left-[23px] top-1 h-3 w-3 rounded-full ring-2 ring-white", s.status === "fallback" ? "bg-sun-400" : "bg-mint-500")} />
                    <div className="flex items-center justify-between gap-2 text-xs font-extrabold text-ink-700">
                      <span className="truncate">{s.step}</span>
                      <span className="flex items-center gap-1 text-ink-400">
                        {s.mode === "llm" ? <Zap className="h-3 w-3" /> : <Cpu className="h-3 w-3" />}
                        {fmtMs(s.duration_ms)}
                      </span>
                    </div>
                    <div className="truncate text-[11px] font-bold text-ink-400">{s.summary}</div>
                  </li>
                ))}
              </ol>
              {traceId && (
                <Link href={`/teacher/trace/${traceId}`} className="mt-3 inline-flex items-center gap-1 text-xs font-extrabold text-curio-600 hover:underline">
                  Open full diagnosis trace <ExternalLink className="h-3 w-3" />
                </Link>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
