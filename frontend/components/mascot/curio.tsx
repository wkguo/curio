"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useId } from "react";

export type CurioMood = "idle" | "thinking" | "happy" | "celebrate" | "curious" | "wave";

/**
 * Curio — a little violet owl with a lightbulb antenna.
 * Pure SVG + Framer Motion; every mood is a small change to eyes, bulb and pose.
 */
export function Curio({ mood = "idle", size = 120, className }: { mood?: CurioMood; size?: number; className?: string }) {
  const uid = useId().replace(/:/g, "");
  const reduce = useReducedMotion();
  const happy = mood === "happy" || mood === "celebrate";
  const pupil =
    mood === "thinking" ? { x: 2.5, y: -3 } : mood === "curious" ? { x: 3, y: 0.5 } : { x: 0, y: 0 };

  const bodyAnim = reduce
    ? {}
    : mood === "celebrate"
      ? { y: [0, -14, 0, -8, 0], rotate: [0, -4, 4, -2, 0] }
      : mood === "thinking"
        ? { rotate: [0, -4, -4, 0], y: [0, -2, 0] }
        : mood === "curious"
          ? { rotate: [0, 6, 6, 0] }
          : { y: [0, -4, 0] };
  const bodyTransition =
    mood === "celebrate"
      ? { duration: 1.1, repeat: Infinity, repeatDelay: 0.4 }
      : { duration: mood === "idle" || mood === "wave" ? 3.2 : 2.4, repeat: Infinity, ease: "easeInOut" as const };

  return (
    <motion.svg
      viewBox="0 0 140 150"
      width={size}
      height={size * (150 / 140)}
      className={className}
      role="img"
      aria-label="Curio the owl"
      animate={bodyAnim}
      transition={bodyTransition}
      style={{ overflow: "visible" }}
    >
      <defs>
        <linearGradient id={`body-${uid}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#A590FF" />
          <stop offset="100%" stopColor="#7152F5" />
        </linearGradient>
        <radialGradient id={`bulb-${uid}`} cx="0.4" cy="0.35" r="0.7">
          <stop offset="0%" stopColor="#FFF6CF" />
          <stop offset="60%" stopColor="#FFD24D" />
          <stop offset="100%" stopColor="#F5A70A" />
        </radialGradient>
      </defs>

      {/* ground shadow */}
      <ellipse cx="70" cy="144" rx="34" ry="5" fill="#1E1B3A" opacity="0.08" />

      {/* antenna + bulb */}
      <path d="M70 30 C 70 20, 76 14, 82 10" stroke="#5631D6" strokeWidth="3.5" fill="none" strokeLinecap="round" />
      <motion.circle
        cx="84"
        cy="9"
        r={mood === "thinking" ? 11 : 8}
        fill="#FFD24D"
        opacity={0.35}
        animate={reduce ? {} : { scale: mood === "thinking" || mood === "celebrate" ? [1, 1.5, 1] : [1, 1.15, 1] }}
        transition={{ duration: mood === "thinking" ? 0.9 : 2.4, repeat: Infinity }}
        style={{ transformOrigin: "84px 9px" }}
      />
      <circle cx="84" cy="9" r="6.5" fill={`url(#bulb-${uid})`} stroke="#E08E00" strokeWidth="1.2" />
      <circle cx="82" cy="7" r="1.8" fill="#fff" opacity="0.9" />

      {/* ear tufts */}
      <path d="M36 44 L30 22 Q 42 28 50 36 Z" fill="#7C5CFF" stroke="#5631D6" strokeWidth="2" strokeLinejoin="round" />
      <path d="M104 44 L110 22 Q 98 28 90 36 Z" fill="#7C5CFF" stroke="#5631D6" strokeWidth="2" strokeLinejoin="round" />

      {/* wings */}
      <motion.path
        d="M28 78 Q 12 92 20 112 Q 30 104 36 96 Z"
        fill="#6842F5"
        stroke="#5631D6"
        strokeWidth="2"
        strokeLinejoin="round"
        animate={reduce ? {} : mood === "celebrate" || mood === "wave" ? { rotate: [0, -28, 0] } : { rotate: 0 }}
        transition={{ duration: 0.6, repeat: Infinity, repeatDelay: mood === "wave" ? 1.2 : 0.2 }}
        style={{ transformOrigin: "34px 84px" }}
      />
      <motion.path
        d="M112 78 Q 128 92 120 112 Q 110 104 104 96 Z"
        fill="#6842F5"
        stroke="#5631D6"
        strokeWidth="2"
        strokeLinejoin="round"
        animate={reduce ? {} : mood === "celebrate" ? { rotate: [0, 28, 0] } : { rotate: 0 }}
        transition={{ duration: 0.6, repeat: Infinity, repeatDelay: 0.2 }}
        style={{ transformOrigin: "106px 84px" }}
      />

      {/* body */}
      <path
        d="M70 30 C 104 30, 116 58, 114 88 C 112 120, 94 138, 70 138 C 46 138, 28 120, 26 88 C 24 58, 36 30, 70 30 Z"
        fill={`url(#body-${uid})`}
        stroke="#5631D6"
        strokeWidth="2.5"
      />
      {/* belly */}
      <path d="M70 84 C 92 84, 98 104, 94 118 C 90 130, 80 134, 70 134 C 60 134, 50 130, 46 118 C 42 104, 48 84, 70 84 Z" fill="#EAE4FF" />
      <path d="M58 104 q 4 4 8 0 M 72 104 q 4 4 8 0 M 64 116 q 4 4 8 0" stroke="#B8A6FF" strokeWidth="2" fill="none" strokeLinecap="round" />

      {/* eye discs */}
      <circle cx="52" cy="66" r="19" fill="#fff" stroke="#5631D6" strokeWidth="2" />
      <circle cx="88" cy="66" r="19" fill="#fff" stroke="#5631D6" strokeWidth="2" />

      {happy ? (
        <>
          <path d="M42 68 Q 52 56 62 68" stroke="#1E1B3A" strokeWidth="4.5" fill="none" strokeLinecap="round" />
          <path d="M78 68 Q 88 56 98 68" stroke="#1E1B3A" strokeWidth="4.5" fill="none" strokeLinecap="round" />
        </>
      ) : (
        <motion.g
          animate={reduce ? {} : { scaleY: [1, 1, 0.1, 1, 1] }}
          transition={{ duration: 4.2, repeat: Infinity, times: [0, 0.9, 0.93, 0.96, 1] }}
          style={{ transformOrigin: "70px 66px" }}
        >
          <motion.g animate={pupil} transition={{ type: "spring", stiffness: 120, damping: 14 }}>
            <circle cx="53" cy="67" r="9" fill="#1E1B3A" />
            <circle cx="89" cy="67" r="9" fill="#1E1B3A" />
            <circle cx="56" cy="63.5" r="3.2" fill="#fff" />
            <circle cx="92" cy="63.5" r="3.2" fill="#fff" />
            <circle cx="50.5" cy="70" r="1.4" fill="#fff" opacity="0.8" />
            <circle cx="86.5" cy="70" r="1.4" fill="#fff" opacity="0.8" />
          </motion.g>
        </motion.g>
      )}

      {/* curious brow */}
      {mood === "curious" && <path d="M78 42 Q 88 38 98 44" stroke="#5631D6" strokeWidth="3" fill="none" strokeLinecap="round" />}

      {/* cheeks */}
      <ellipse cx="38" cy="86" rx="7" ry="4.5" fill="#FF8FB8" opacity="0.55" />
      <ellipse cx="102" cy="86" rx="7" ry="4.5" fill="#FF8FB8" opacity="0.55" />

      {/* beak */}
      <path d="M64 80 Q 70 76 76 80 Q 72 90 70 90 Q 68 90 64 80 Z" fill="#FFC53D" stroke="#E08E00" strokeWidth="1.6" strokeLinejoin="round" />

      {/* feet */}
      <ellipse cx="58" cy="139" rx="8" ry="4" fill="#FFC53D" stroke="#E08E00" strokeWidth="1.5" />
      <ellipse cx="82" cy="139" rx="8" ry="4" fill="#FFC53D" stroke="#E08E00" strokeWidth="1.5" />

      {/* celebrate sparkles */}
      {mood === "celebrate" &&
        [
          [14, 30],
          [126, 34],
          [8, 70],
          [132, 76],
        ].map(([x, y], i) => (
          <motion.path
            key={i}
            d={`M${x} ${y - 7} L${x + 2} ${y - 2} L${x + 7} ${y} L${x + 2} ${y + 2} L${x} ${y + 7} L${x - 2} ${y + 2} L${x - 7} ${y} L${x - 2} ${y - 2} Z`}
            fill={["#FFC53D", "#1FB978", "#FF6FB1", "#2E97F5"][i]}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: [0, 1.2, 0], opacity: [0, 1, 0] }}
            transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.25 }}
            style={{ transformOrigin: `${x}px ${y}px` }}
          />
        ))}
    </motion.svg>
  );
}

/** Speech bubble next to Curio. */
export function CurioSays({ children, mood = "idle", size = 64 }: { children: React.ReactNode; mood?: CurioMood; size?: number }) {
  return (
    <div className="flex items-end gap-3">
      <Curio mood={mood} size={size} className="shrink-0" />
      <div className="relative mb-3 rounded-3xl rounded-bl-md border-2 border-curio-100 bg-white px-4 py-3 text-[15px] font-bold leading-snug text-ink-700 shadow-soft">
        {children}
      </div>
    </div>
  );
}
