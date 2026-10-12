"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";

const COLORS = ["#7C5CFF", "#1FB978", "#FFC53D", "#FF6B3D", "#2E97F5", "#FF6FB1"];

/** Lightweight confetti burst (no dependency). Renders once when mounted. */
export function Confetti({ pieces = 60 }: { pieces?: number }) {
  const bits = useMemo(
    () =>
      Array.from({ length: pieces }, (_, i) => ({
        id: i,
        x: (Math.random() - 0.5) * 900,
        y: -(Math.random() * 380 + 160),
        r: Math.random() * 720 - 360,
        c: COLORS[i % COLORS.length],
        w: 6 + Math.random() * 8,
        h: 8 + Math.random() * 10,
        d: Math.random() * 0.25,
        round: Math.random() > 0.6,
      })),
    [pieces],
  );
  return (
    <div className="pointer-events-none absolute inset-0 z-30 overflow-visible" aria-hidden>
      {bits.map((b) => (
        <motion.span
          key={b.id}
          className="absolute left-1/2 top-1/2"
          style={{ width: b.w, height: b.round ? b.w : b.h, background: b.c, borderRadius: b.round ? 999 : 3 }}
          initial={{ x: 0, y: 0, opacity: 1, rotate: 0, scale: 0.6 }}
          animate={{ x: b.x, y: [0, b.y, b.y + 520], opacity: [1, 1, 0], rotate: b.r, scale: 1 }}
          transition={{ duration: 2.2, delay: b.d, ease: [0.2, 0.7, 0.4, 1], times: [0, 0.35, 1] }}
        />
      ))}
    </div>
  );
}
