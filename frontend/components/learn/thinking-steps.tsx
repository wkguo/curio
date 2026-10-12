"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Check } from "lucide-react";
import { useEffect, useState } from "react";

import { Curio } from "@/components/mascot/curio";
import { cn } from "@/lib/utils";

export const SUBMIT_STEPS = ["Checking your answer", "Comparing reasoning", "Finding the concept", "Looking for misconceptions", "Preparing a follow-up"];
export const TRANSFER_STEPS = ["Reading your new answer", "Checking the same idea in a new place", "Updating your mastery"];

/**
 * "Curio is thinking..." (spec §14). Steps tick at a steady pace; `onDone` fires once
 * every step is shown AND `ready` is true (the request finished), so fast responses
 * still get a readable animation and slow ones never stall on a fake 100%.
 */
export function ThinkingSteps({ steps, ready, onDone, pace = 520 }: { steps: string[]; ready: boolean; onDone: () => void; pace?: number }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (i < steps.length - 1) {
      const t = setTimeout(() => setI((x) => x + 1), pace);
      return () => clearTimeout(t);
    }
    if (ready) {
      const t = setTimeout(onDone, pace);
      return () => clearTimeout(t);
    }
  }, [i, ready, steps.length, pace, onDone]);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} className="card-base flex items-center gap-5 p-5 sm:p-6">
      <Curio mood="thinking" size={78} className="shrink-0" />
      <div className="flex-1">
        <div className="shimmer-text mb-3 text-lg font-black">Curio is thinking…</div>
        <ul className="space-y-1.5">
          {steps.map((s, k) => {
            const done = k < i || (k === i && ready && i === steps.length - 1);
            const active = k === i && !done;
            return (
              <li key={s} className={cn("flex items-center gap-2.5 text-[15px] font-bold transition-colors", done ? "text-ink-700" : active ? "text-curio-600" : "text-ink-300")}>
                <span className={cn("grid h-5 w-5 place-items-center rounded-full", done ? "bg-mint-500 text-white" : active ? "bg-curio-100" : "bg-ink-100")}>
                  <AnimatePresence mode="wait">
                    {done ? (
                      <motion.span key="d" initial={{ scale: 0 }} animate={{ scale: 1 }}>
                        <Check className="h-3.5 w-3.5" strokeWidth={3.5} />
                      </motion.span>
                    ) : active ? (
                      <motion.span key="a" className="h-2 w-2 rounded-full bg-curio-500" animate={{ scale: [1, 1.6, 1] }} transition={{ repeat: Infinity, duration: 0.8 }} />
                    ) : null}
                  </AnimatePresence>
                </span>
                {s}
              </li>
            );
          })}
        </ul>
      </div>
    </motion.div>
  );
}
