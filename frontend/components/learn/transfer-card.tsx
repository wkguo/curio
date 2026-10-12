"use client";

import { motion } from "framer-motion";
import { Rocket, ShieldCheck } from "lucide-react";

import { Emoji } from "@/components/ui/emoji";
import { Tooltip } from "@/components/ui/tooltip";
import type { PublicQuestion, QuestionQuality } from "@/types/api";

/** The "Question Back" card (spec §9): same concept, new surface context. */
export function TransferCard({ q, quality, children }: { q: PublicQuestion; quality?: QuestionQuality; children?: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16, rotate: -0.6 }}
      animate={{ opacity: 1, y: 0, rotate: 0 }}
      transition={{ type: "spring", stiffness: 180, damping: 18 }}
      className="relative overflow-hidden rounded-3xl border-2 border-sky-200 bg-gradient-to-br from-sky-50 via-white to-curio-50 p-5 shadow-float sm:p-6"
    >
      <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-sky-200/40 blur-2xl" />
      <div className="relative mb-3 flex flex-wrap items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-500 px-3 py-1 text-xs font-extrabold text-white">
          <Rocket className="h-3.5 w-3.5" /> Transfer challenge · same idea, new situation
        </span>
        {quality && (
          <Tooltip
            content={
              <div className="space-y-0.5">
                <div>Question quality verifier</div>
                {["same_concept", "age_appropriate", "answerable", "curriculum_aligned", "not_a_repeat"].map((k) => (
                  <div key={k}>
                    {(quality as any)[k] ? "✓" : "✗"} {k.replace(/_/g, " ")}
                  </div>
                ))}
              </div>
            }
          >
            <span className="inline-flex cursor-help items-center gap-1 rounded-full bg-mint-100 px-2.5 py-1 text-[11px] font-extrabold text-mint-700">
              <ShieldCheck className="h-3.5 w-3.5" /> {quality.approved ? "Verified question" : "Curated question"}
            </span>
          </Tooltip>
        )}
      </div>
      <div className="relative flex gap-4">
        <div className="grid h-20 w-20 shrink-0 place-items-center rounded-3xl bg-white shadow-soft">
          <Emoji name={q.emoji} size={54} />
        </div>
        <p className="text-[18px] font-extrabold leading-snug text-ink-900 sm:text-[19px]">{q.prompt}</p>
      </div>
      {children && <div className="relative mt-4">{children}</div>}
    </motion.div>
  );
}
