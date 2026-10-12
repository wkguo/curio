"use client";

import { animate, useMotionValue, useTransform, motion } from "framer-motion";
import { useEffect } from "react";

/** Counts from `from` to `value`. `format` turns the number into display text. */
export function AnimatedNumber({
  value,
  from = 0,
  format = (n) => Math.round(n).toString(),
  duration = 1.1,
  delay = 0,
}: {
  value: number;
  from?: number;
  format?: (n: number) => string;
  duration?: number;
  delay?: number;
}) {
  const mv = useMotionValue(from);
  const text = useTransform(mv, (v) => format(v));
  useEffect(() => {
    const controls = animate(mv, value, { duration, delay, ease: [0.22, 1, 0.36, 1] });
    return () => controls.stop();
  }, [value, mv, duration, delay]);
  return <motion.span className="tabular-nums">{text}</motion.span>;
}
