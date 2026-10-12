"use client";

import { motion } from "framer-motion";

import { Emoji } from "@/components/ui/emoji";
import { CLASSIFICATION, PHASE, STRATEGY } from "@/lib/labels";
import { cn } from "@/lib/utils";
import type { LearningState } from "@/types/api";

/** Compact learning state (proposal): concept · misconception · intervention · status, plus the transition log. */
export function LearningStateCard({ state, compact }: { state: LearningState; compact?: boolean }) {
  const ph = PHASE[state.phase];
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2.5">
        <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-extrabold", ph.tone)}>
          <Emoji name={ph.emoji} size={16} /> {ph.label}
        </span>
        {state.classification && (
          <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-extrabold", CLASSIFICATION[state.classification].tone)}>
            {CLASSIFICATION[state.classification].label}
          </span>
        )}
      </div>
      <dl className="grid grid-cols-[96px_1fr] gap-x-2 gap-y-1 text-xs">
        <dt className="font-extrabold text-ink-400">Concept</dt>
        <dd className="font-bold text-ink-800">{state.concept_name}</dd>
        <dt className="font-extrabold text-ink-400">Misconception</dt>
        <dd className="font-bold text-ink-800">{state.misconception_label ?? "—"}</dd>
        <dt className="font-extrabold text-ink-400">Intervention</dt>
        <dd className="font-bold text-ink-800">{state.intervention ? STRATEGY[state.intervention]?.label : "—"}</dd>
        <dt className="font-extrabold text-ink-400">Mastery</dt>
        <dd className="font-bold text-ink-800">
          {Math.round(state.mastery * 100)}% · {state.transfer_attempts} transfer attempt{state.transfer_attempts === 1 ? "" : "s"}
        </dd>
      </dl>
      {!compact && state.history.length > 0 && (
        <ol className="relative space-y-1.5 border-l-2 border-dashed border-ink-200 pl-4">
          {state.history.map((h, i) => (
            <motion.li key={i} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} className="relative text-[11px] font-bold text-ink-500">
              <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-curio-400 ring-2 ring-white" />
              <span className="text-ink-800">
                {PHASE[h.from_phase].label} → {PHASE[h.to_phase].label}
              </span>
              <div className="text-ink-400">{h.trigger}</div>
            </motion.li>
          ))}
        </ol>
      )}
    </div>
  );
}
