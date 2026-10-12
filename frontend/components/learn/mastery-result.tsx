"use client";

import { motion } from "framer-motion";
import { ArrowRight, Microscope } from "lucide-react";
import Link from "next/link";

import { Curio } from "@/components/mascot/curio";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { Button } from "@/components/ui/button";
import { Confetti } from "@/components/ui/confetti";
import { Emoji } from "@/components/ui/emoji";
import { Progress } from "@/components/ui/progress";
import { RichText } from "@/components/ui/rich-text";
import { cn } from "@/lib/utils";
import type { TransferResponse } from "@/types/api";

const COPY = {
  mastered: { badge: "Concept mastery confirmed", emoji: "check_mark_button", tone: "mint", mood: "celebrate" },
  verified: { badge: "Understanding verified — keep practising", emoji: "check_mark_button", tone: "mint", mood: "happy" },
  reteach: { badge: "Not yet — let's look again", emoji: "books", tone: "sun", mood: "curious" },
  revisit: { badge: "We'll come back to this one", emoji: "seedling", tone: "sun", mood: "curious" },
} as const;

/** Result of the question back. `reteach` is compact (the loop continues below it). */
export function MasteryResult({ result, onNext, isLast }: { result: TransferResponse; onNext: () => void; isLast: boolean }) {
  const ch = result.mastery_change;
  const copy = COPY[result.next_state] ?? COPY.verified;
  const ok = result.mastery_confirmed;
  const compact = result.next_state === "reteach";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 20 }}
      className={cn(
        "relative rounded-3xl border-2 shadow-float",
        compact ? "p-4" : "p-6",
        ok ? "border-mint-200 bg-gradient-to-br from-mint-50 via-white to-sun-50" : "border-sun-200 bg-gradient-to-br from-sun-50 to-white",
      )}
    >
      {result.next_state === "mastered" && <Confetti />}
      <div className={cn("relative flex", compact ? "items-center gap-4" : "flex-col items-center text-center")}>
        <Curio size={compact ? 56 : 96} mood={copy.mood} />
        <div className={cn(compact ? "flex-1" : "flex flex-col items-center")}>
          <div className={cn("mt-2 inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-extrabold", ok ? "bg-mint-500 text-white" : "bg-sun-400 text-ink-900")}>
            <Emoji name={copy.emoji} size={16} />
            {copy.badge}
            {result.attempt > 1 && <span className="opacity-80">· attempt {result.attempt}</span>}
          </div>
          {ch && <h3 className={cn("font-black text-ink-900", compact ? "mt-1 text-lg" : "mt-3 text-2xl")}>{ch.concept_name}</h3>}

          {ch && !compact && (
            <div className="mt-4 w-full max-w-sm">
              <div className="mb-2 flex items-baseline justify-center gap-3 font-black tabular-nums">
                <span className="text-xl text-ink-400">{Math.round(ch.before * 100)}%</span>
                <ArrowRight className="h-5 w-5 text-ink-300" />
                <span className={cn("text-4xl", ok ? "text-mint-600" : "text-sun-600")}>
                  <AnimatedNumber value={ch.after * 100} from={ch.before * 100} format={(n) => `${Math.round(n)}%`} delay={0.3} duration={1.6} />
                </span>
              </div>
              <Progress value={ch.after} from={ch.before} color={ok ? "#1FB978" : "#F5A70A"} height={16} delay={0.3} />
            </div>
          )}

          <p className={cn("font-bold leading-relaxed text-ink-700", compact ? "mt-1 text-sm" : "mt-5 max-w-lg text-[15px]")}>
            <RichText text={result.feedback} />
          </p>
          {result.next_state === "verified" && (
            <p className="mt-2 max-w-md text-xs font-bold text-ink-400">Mastery is granted only after verified transfer AND a high enough score — one more verified answer will get you there.</p>
          )}
          {!compact && <div className="mt-2 text-sm font-extrabold text-sky-600">+{result.xp_earned} XP</div>}
        </div>

        {!compact && (
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Button onClick={onNext} size="lg" variant={ok ? "mint" : "default"}>
              {isLast ? "Finish session" : "Next question"} <ArrowRight />
            </Button>
            <Button asChild variant="secondary" size="lg">
              <Link href={`/teacher/trace/${result.trace_id}`}>
                <Microscope /> See how Curio decided
              </Link>
            </Button>
          </div>
        )}
      </div>
    </motion.div>
  );
}
