"use client";

import { motion } from "framer-motion";
import { HeartHandshake, Lock, MessageCircleWarning, ShieldCheck } from "lucide-react";

import { Curio } from "@/components/mascot/curio";
import { cn } from "@/lib/utils";
import type { SafetyNotice } from "@/types/api";

const STYLE: Record<SafetyNotice["category"], { icon: typeof Lock; tone: string; title: string }> = {
  pii: { icon: Lock, tone: "border-sky-200 bg-sky-50", title: "Privacy tip" },
  unsafe: { icon: HeartHandshake, tone: "border-curio-300 bg-curio-50", title: "You're not alone" },
  prompt_injection: { icon: ShieldCheck, tone: "border-ink-200 bg-white", title: "Science only" },
  off_topic: { icon: MessageCircleWarning, tone: "border-ink-200 bg-white", title: "Back to science" },
  answer_request: { icon: MessageCircleWarning, tone: "border-sun-200 bg-sun-50", title: "Let's work it out" },
  language: { icon: MessageCircleWarning, tone: "border-ink-200 bg-white", title: "English, please" },
};

/** Message from the safety & privacy layer (proposal module 6). */
export function SafetyBubble({ category, text }: { category: SafetyNotice["category"]; text: string }) {
  const s = STYLE[category];
  const Icon = s.icon;
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex items-end gap-2.5">
      <div className="w-10 shrink-0">
        <Curio size={40} mood="curious" />
      </div>
      <div className={cn("max-w-[85%] rounded-3xl rounded-bl-lg border-2 px-4 py-3", s.tone)}>
        <div className="mb-1 flex items-center gap-1.5 text-[11px] font-extrabold uppercase tracking-wider text-ink-500">
          <Icon className="h-3.5 w-3.5" /> {s.title}
        </div>
        <p className="text-[15px] font-semibold leading-relaxed text-ink-700">{text}</p>
      </div>
    </motion.div>
  );
}
