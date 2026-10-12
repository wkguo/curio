"use client";

import { motion } from "framer-motion";
import { ArrowDown } from "lucide-react";

import { cn } from "@/lib/utils";

export interface PipelineNode {
  key: string;
  title: string;
  emoji?: React.ReactNode;
  value: React.ReactNode;
  tone: "neutral" | "good" | "bad" | "warn" | "brand" | "sky";
  stepKeys?: string[];
}

const TONE: Record<PipelineNode["tone"], string> = {
  neutral: "border-ink-200 bg-white",
  good: "border-mint-200 bg-mint-50",
  bad: "border-coral-200 bg-coral-50",
  warn: "border-sun-200 bg-sun-50",
  brand: "border-curio-200 bg-curio-50",
  sky: "border-sky-200 bg-sky-50",
};

/** "AI Diagnosis Trace" (spec §13): Student Answer ↓ Answer Correct ↓ … ↓ Mastery. */
export function TracePipeline({ nodes, active, onSelect }: { nodes: PipelineNode[]; active?: string; onSelect: (n: PipelineNode) => void }) {
  return (
    <ol className="flex flex-col items-stretch">
      {nodes.map((n, i) => (
        <li key={n.key} className="flex flex-col items-center">
          <motion.button
            initial={{ opacity: 0, y: 14, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: 0.12 * i, type: "spring", stiffness: 220, damping: 22 }}
            onClick={() => onSelect(n)}
            className={cn(
              "w-full rounded-3xl border-2 px-5 py-4 text-left transition hover:-translate-y-0.5 hover:shadow-float",
              TONE[n.tone],
              active === n.key && "ring-4 ring-curio-200",
            )}
          >
            <div className="flex items-center gap-3">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-white shadow-soft">{n.emoji}</span>
              <div className="min-w-0 flex-1">
                <div className="label-caps">{n.title}</div>
                <div className="mt-0.5 text-[15px] font-extrabold text-ink-900">{n.value}</div>
              </div>
            </div>
          </motion.button>
          {i < nodes.length - 1 && (
            <motion.div initial={{ opacity: 0, scaleY: 0 }} animate={{ opacity: 1, scaleY: 1 }} transition={{ delay: 0.12 * i + 0.08 }} className="flex h-8 origin-top flex-col items-center">
              <div className="w-0.5 flex-1 bg-gradient-to-b from-curio-300 to-curio-200" />
              <ArrowDown className="-mt-1 h-4 w-4 text-curio-400" strokeWidth={3} />
            </motion.div>
          )}
        </li>
      ))}
    </ol>
  );
}
