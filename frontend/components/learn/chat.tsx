"use client";

import { motion } from "framer-motion";

import { Curio, type CurioMood } from "@/components/mascot/curio";
import { Emoji } from "@/components/ui/emoji";
import { RichText } from "@/components/ui/rich-text";
import { cn } from "@/lib/utils";

export function CurioBubble({ text, highlight, showAvatar = true, mood = "idle" }: { text: string; highlight?: boolean; showAvatar?: boolean; mood?: CurioMood }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ type: "spring", stiffness: 260, damping: 22 }} className="flex items-end gap-2.5">
      <div className="w-10 shrink-0">{showAvatar && <Curio size={40} mood={mood} />}</div>
      <div
        className={cn(
          "max-w-[85%] rounded-3xl rounded-bl-lg px-4 py-3 text-[15.5px] font-semibold leading-relaxed text-ink-700",
          highlight ? "border-2 border-curio-300 bg-curio-50 text-ink-800 shadow-glow" : "border border-ink-200/80 bg-white shadow-soft",
        )}
      >
        {highlight && <div className="label-caps mb-1 !text-curio-500">Your turn</div>}
        <RichText text={text} />
      </div>
    </motion.div>
  );
}

export function StudentBubble({ text, avatar = "fox" }: { text: string; avatar?: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex items-end justify-end gap-2.5">
      <div className="max-w-[85%] rounded-3xl rounded-br-lg bg-curio-500 px-4 py-3 text-[15.5px] font-bold leading-relaxed text-white shadow-[0_3px_0_0_#5631D6]">{text}</div>
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-white shadow-soft ring-1 ring-ink-200">
        <Emoji name={avatar} size={28} />
      </div>
    </motion.div>
  );
}

export function TypingBubble() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-end gap-2.5">
      <div className="w-10 shrink-0">
        <Curio size={40} mood="thinking" />
      </div>
      <div className="flex gap-1.5 rounded-3xl rounded-bl-lg border border-ink-200/80 bg-white px-4 py-4 shadow-soft">
        {[0, 1, 2].map((i) => (
          <motion.span key={i} className="h-2 w-2 rounded-full bg-curio-300" animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.15 }} />
        ))}
      </div>
    </motion.div>
  );
}
