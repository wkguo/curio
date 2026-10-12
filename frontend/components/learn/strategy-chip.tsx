"use client";

import { motion } from "framer-motion";

import { Tooltip } from "@/components/ui/tooltip";
import { STRATEGY } from "@/lib/labels";
import { cn } from "@/lib/utils";
import type { TeachingStrategy } from "@/types/api";

export function StrategyChip({ strategy, reason }: { strategy: TeachingStrategy; reason?: string }) {
  const s = STRATEGY[strategy];
  const Icon = s.icon;
  return (
    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex justify-center">
      <Tooltip content={reason || s.blurb}>
        <span className={cn("inline-flex cursor-help items-center gap-2 rounded-full px-3.5 py-1.5 text-xs font-extrabold ring-1 ring-inset ring-black/5", s.tone)}>
          <Icon className="h-3.5 w-3.5" strokeWidth={2.6} />
          Teaching strategy · {s.label}
        </span>
      </Tooltip>
    </motion.div>
  );
}
