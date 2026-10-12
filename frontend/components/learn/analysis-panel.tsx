"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Search, XCircle } from "lucide-react";

import { Curio } from "@/components/mascot/curio";
import { RichText } from "@/components/ui/rich-text";
import { cn } from "@/lib/utils";
import type { AnalysisFeedback, Verification } from "@/types/api";

const item = { hidden: { opacity: 0, x: -8 }, show: { opacity: 1, x: 0 } };

/** "Curio is checking your reasoning…" result panel (spec §4.2). Never reveals the full answer. */
export function AnalysisPanel({ feedback, verification }: { feedback: AnalysisFeedback; verification?: Verification | null }) {
  const tone = feedback.tone;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "overflow-hidden rounded-3xl border-2 bg-white shadow-soft",
        tone === "celebrate" ? "border-mint-200" : tone === "encourage" ? "border-sun-200" : "border-curio-200",
      )}
    >
      <div className={cn("flex items-center gap-3 px-5 py-3.5", tone === "celebrate" ? "bg-mint-50" : tone === "encourage" ? "bg-sun-50" : "bg-curio-50")}>
        <Curio size={44} mood={tone === "celebrate" ? "happy" : "curious"} />
        <div className="flex-1">
          <div className="label-caps">Curio checked your reasoning</div>
          <div className="text-lg font-black text-ink-900">{feedback.headline}</div>
        </div>
        {verification && verification.classification !== "unclear" && (
          <div className="hidden gap-1.5 sm:flex">
            <Verdict ok={verification.answer_correct} label="Answer" />
            <Verdict ok={verification.reasoning_correct} label="Reasoning" />
          </div>
        )}
      </div>

      <motion.ul variants={{ show: { transition: { staggerChildren: 0.18, delayChildren: 0.15 } } }} initial="hidden" animate="show" className="space-y-3 px-5 py-4">
        {feedback.strengths.map((s) => (
          <motion.li key={s} variants={item} className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-mint-500" strokeWidth={2.6} />
            <span className="text-[15px] font-bold text-ink-700">{s}</span>
          </motion.li>
        ))}
        {feedback.concerns.map((c) => (
          <motion.li key={c.claim} variants={item} className="rounded-2xl bg-sun-50 p-3.5 ring-1 ring-sun-200">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-sun-600" strokeWidth={2.6} />
              <div>
                <div className="text-[15px] font-extrabold text-ink-800">But one idea needs another look:</div>
                <blockquote className="my-1.5 border-l-4 border-sun-400 pl-3 text-[15px] font-bold italic text-ink-700">“{c.claim}”</blockquote>
                <p className="text-sm font-semibold text-ink-600">
                  <RichText text={c.note} />
                </p>
              </div>
            </div>
          </motion.li>
        ))}
        {feedback.concerns.length === 0 && feedback.nudge && (
          <motion.li variants={item} className="flex items-start gap-3">
            <Search className="mt-0.5 h-5 w-5 shrink-0 text-curio-500" strokeWidth={2.6} />
            <span className="text-[15px] font-bold text-ink-600">
              <RichText text={feedback.nudge} />
            </span>
          </motion.li>
        )}
      </motion.ul>
    </motion.div>
  );
}

function Verdict({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-extrabold", ok ? "bg-mint-100 text-mint-700" : "bg-coral-100 text-coral-700")}>
      {ok ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}
      {label}
    </span>
  );
}
