"use client";

import { motion } from "framer-motion";

import { cn } from "@/lib/utils";

/** Rounded progress bar that animates from `from` to `value` (0..1). */
export function Progress({
  value,
  from,
  color = "#7C5CFF",
  className,
  height = 12,
  delay = 0,
}: {
  value: number;
  from?: number;
  color?: string;
  className?: string;
  height?: number;
  delay?: number;
}) {
  const v = Math.max(0, Math.min(1, value));
  return (
    <div className={cn("relative w-full overflow-hidden rounded-full bg-ink-100", className)} style={{ height }} role="progressbar" aria-valuenow={Math.round(v * 100)} aria-valuemin={0} aria-valuemax={100}>
      <motion.div
        className="absolute inset-y-0 left-0 rounded-full"
        style={{ background: color }}
        initial={{ width: `${(from ?? 0) * 100}%` }}
        animate={{ width: `${v * 100}%` }}
        transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1], delay }}
      >
        <div className="absolute inset-x-1.5 top-[3px] h-[3px] rounded-full bg-white/35" />
      </motion.div>
    </div>
  );
}
