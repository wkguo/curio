"use client";

import { motion } from "framer-motion";

import { Tooltip } from "@/components/ui/tooltip";

const SEGMENTS = [
  { key: "answer_ok_reasoning_ok", label: "Right answer, right reasoning", color: "#1FB978" },
  { key: "answer_ok_reasoning_wrong", label: "Right answer, flawed reasoning", color: "#F5A70A" },
  { key: "answer_wrong_reasoning_ok", label: "Wrong answer, partial reasoning", color: "#57B2FF" },
  { key: "answer_wrong_reasoning_wrong", label: "Wrong answer", color: "#FF6B3D" },
];

/** The core Curio insight as one part-to-whole bar + hero number. */
export function AnswerVsReasoning({ counts }: { counts: Record<string, number> }) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
  const rightAnswers = (counts.answer_ok_reasoning_ok ?? 0) + (counts.answer_ok_reasoning_wrong ?? 0);
  const hidden = rightAnswers ? (counts.answer_ok_reasoning_wrong ?? 0) / rightAnswers : 0;
  return (
    <div>
      <div className="flex items-end gap-3">
        <div className="text-5xl font-black text-sun-600">{Math.round(hidden * 100)}%</div>
        <p className="mb-1.5 max-w-xs text-sm font-bold leading-snug text-ink-600">
          of <b className="text-ink-900">correct answers</b> hid a reasoning gap a normal quiz would have missed.
        </p>
      </div>
      <div className="mt-5 flex h-9 w-full gap-[2px] overflow-hidden rounded-xl">
        {SEGMENTS.map((s, i) => {
          const v = counts[s.key] ?? 0;
          if (!v) return null;
          return (
            <Tooltip key={s.key} content={`${s.label}: ${v} (${Math.round((v / total) * 100)}%)`}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(v / total) * 100}%` }}
                transition={{ duration: 0.9, delay: i * 0.1, ease: [0.22, 1, 0.36, 1] }}
                className="grid h-full cursor-help place-items-center text-xs font-black text-white first:rounded-l-xl last:rounded-r-xl"
                style={{ background: s.color }}
              >
                {v / total > 0.08 ? `${Math.round((v / total) * 100)}%` : ""}
              </motion.div>
            </Tooltip>
          );
        })}
      </div>
      <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5">
        {SEGMENTS.map((s) => (
          <li key={s.key} className="flex items-center gap-2 text-xs font-bold text-ink-600">
            <span className="h-3 w-3 shrink-0 rounded" style={{ background: s.color }} />
            <span className="flex-1">{s.label}</span>
            <span className="tabular-nums text-ink-400">{counts[s.key] ?? 0}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
