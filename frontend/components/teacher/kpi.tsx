"use client";

import { motion } from "framer-motion";

import { AnimatedNumber } from "@/components/ui/animated-number";
import { Emoji } from "@/components/ui/emoji";

export function Kpi({ emoji, label, value, format, sub, delay = 0, tint }: { emoji: string; label: string; value: number; format?: (n: number) => string; sub?: string; delay?: number; tint: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }} className="card-base relative overflow-hidden p-5">
      <div className="absolute -right-5 -top-5 h-20 w-20 rounded-full opacity-60" style={{ background: tint }} />
      <Emoji name={emoji} size={34} className="relative" />
      <div className="relative mt-3 text-3xl font-black text-ink-900">
        <AnimatedNumber value={value} format={format} />
      </div>
      <div className="relative text-sm font-extrabold text-ink-500">{label}</div>
      {sub && <div className="relative mt-0.5 text-xs font-bold text-ink-400">{sub}</div>}
    </motion.div>
  );
}
