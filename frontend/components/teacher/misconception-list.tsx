"use client";

import { motion } from "framer-motion";

import type { MisconceptionStat } from "@/types/api";

export function MisconceptionList({ items, topicColor, students }: { items: MisconceptionStat[]; topicColor: Record<string, string>; students: number }) {
  const max = Math.max(1, ...items.map((i) => i.students));
  return (
    <ol className="space-y-3">
      {items.map((m, i) => (
        <motion.li key={m.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="grid grid-cols-[28px_1fr_auto] items-center gap-3">
          <span className="grid h-7 w-7 place-items-center rounded-full bg-ink-100 text-xs font-black text-ink-600">{i + 1}</span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="truncate text-[15px] font-extrabold text-ink-900">{m.label}</span>
              <span className="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-extrabold text-white" style={{ background: topicColor[m.topic_id] ?? "#7C5CFF" }}>
                {m.topic_name}
              </span>
            </div>
            <div className="mt-1 flex items-center gap-2">
              <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-ink-100">
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: topicColor[m.topic_id] ?? "#7C5CFF" }}
                  initial={{ width: 0 }}
                  animate={{ width: `${(m.students / max) * 100}%` }}
                  transition={{ duration: 0.8, delay: 0.1 + i * 0.05 }}
                />
              </div>
              <span className="w-24 shrink-0 text-right text-[11px] font-bold text-ink-400">{Math.round(m.resolved_rate * 100)}% resolved</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-lg font-black tabular-nums text-ink-900">{m.students}</div>
            <div className="text-[10px] font-extrabold uppercase text-ink-400">of {students}</div>
          </div>
        </motion.li>
      ))}
    </ol>
  );
}
