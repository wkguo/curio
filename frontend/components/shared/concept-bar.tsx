"use client";

import { motion } from "framer-motion";

import { StatusIcon } from "@/components/shared/status-icon";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { Emoji } from "@/components/ui/emoji";
import { Progress } from "@/components/ui/progress";
import { STATUS } from "@/lib/labels";
import { cn } from "@/lib/utils";
import type { ConceptNode } from "@/types/api";

/** One row of the "Temperature ████████ 91%" mastery list (spec §12). */
export function ConceptBar({ concept, highlight, from, delay = 0 }: { concept: ConceptNode; highlight?: boolean; from?: number; delay?: number }) {
  const color = STATUS[concept.status].color;
  return (
    <motion.div
      layout
      className={cn("rounded-2xl px-3 py-2.5 transition", highlight ? "bg-curio-50 ring-2 ring-curio-200" : "hover:bg-ink-50")}
    >
      <div className="mb-1.5 flex items-center gap-2.5">
        <Emoji name={concept.emoji} size={22} />
        <span className="flex-1 truncate text-sm font-extrabold text-ink-800">{concept.name}</span>
        <StatusIcon status={concept.status} className="h-4 w-4" />
        <span className="w-10 text-right text-sm font-black tabular-nums text-ink-700">
          <AnimatedNumber value={concept.mastery * 100} from={(from ?? concept.mastery) * 100} format={(n) => `${Math.round(n)}%`} delay={delay} />
        </span>
      </div>
      <Progress value={concept.mastery} from={from} color={concept.status === "locked" ? "#C9C7D8" : color} height={9} delay={delay} />
    </motion.div>
  );
}
