"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Lightbulb, Star } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Emoji } from "@/components/ui/emoji";
import { cn } from "@/lib/utils";
import type { QuestionCard as Q } from "@/types/api";

export function QuestionCard({ q, color, compact }: { q: Q; color: string; compact?: boolean }) {
  const [hints, setHints] = useState(0);
  return (
    <motion.div layout className="card-base relative overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-1.5" style={{ background: color }} />
      <div className={cn("flex gap-5 p-5 sm:p-6", compact && "items-center py-4")}>
        <motion.div
          layout
          className={cn("grid shrink-0 place-items-center rounded-3xl", compact ? "h-14 w-14" : "h-20 w-20 sm:h-28 sm:w-28")}
          style={{ background: `${color}14` }}
        >
          <Emoji name={q.emoji} size={compact ? 36 : 60} className={compact ? "" : "animate-float-y"} />
        </motion.div>
        <div className="min-w-0 flex-1">
          {!compact && (
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge variant="outline">{q.concept_name}</Badge>
              <span className="flex items-center gap-0.5" aria-label={`Difficulty ${q.difficulty} of 5`}>
                {Array.from({ length: 3 }).map((_, i) => (
                  <Star key={i} className={cn("h-3.5 w-3.5", i < Math.min(3, q.difficulty) ? "fill-sun-400 text-sun-400" : "text-ink-200")} />
                ))}
              </span>
            </div>
          )}
          <p className={cn("font-extrabold leading-snug text-ink-900", compact ? "line-clamp-2 text-[15px]" : "text-[19px] sm:text-xl")}>{q.prompt}</p>
          {!compact && q.hints.length > 0 && (
            <div className="mt-3">
              <AnimatePresence>
                {q.hints.slice(0, hints).map((h) => (
                  <motion.div key={h} initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mb-2 flex items-start gap-2 rounded-2xl bg-sun-50 px-3 py-2 text-sm font-bold text-sun-700">
                    <Lightbulb className="mt-0.5 h-4 w-4 shrink-0" /> {h}
                  </motion.div>
                ))}
              </AnimatePresence>
              {hints < q.hints.length && (
                <button onClick={() => setHints((h) => h + 1)} className="inline-flex items-center gap-1.5 text-sm font-extrabold text-sun-600 hover:text-sun-700">
                  <Lightbulb className="h-4 w-4" /> Need a hint?
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
