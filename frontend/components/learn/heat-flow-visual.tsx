"use client";

import { motion } from "framer-motion";

/**
 * VISUAL_EXPLANATION for heat conduction: heat flows from a warm hand into two
 * spoons at the same room temperature — big fast arrows for metal, small slow
 * arrows for wood.
 */
export function HeatFlowVisual() {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="ml-12 overflow-hidden rounded-3xl border border-ink-200 bg-gradient-to-b from-sun-50 to-white p-4 shadow-soft">
      <svg viewBox="0 0 440 190" className="w-full" role="img" aria-label="Heat flows faster from a hand into a metal spoon than into a wooden spoon">
        <defs>
          <linearGradient id="metal" x1="0" x2="1">
            <stop offset="0" stopColor="#C9CFDB" />
            <stop offset=".5" stopColor="#F4F6FA" />
            <stop offset="1" stopColor="#AEB6C6" />
          </linearGradient>
          <linearGradient id="wood" x1="0" x2="1">
            <stop offset="0" stopColor="#C98A55" />
            <stop offset="1" stopColor="#A86A3A" />
          </linearGradient>
          <marker id="arrowHead" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto">
            <path d="M0 0 L10 5 L0 10 z" fill="#FF6B3D" />
          </marker>
        </defs>
        {/* hand */}
        <g transform="translate(20 40)">
          <rect x="0" y="20" width="84" height="78" rx="34" fill="#FFD3B0" stroke="#E7A57A" strokeWidth="3" />
          <rect x="70" y="30" width="46" height="18" rx="9" fill="#FFD3B0" stroke="#E7A57A" strokeWidth="3" />
          <rect x="70" y="70" width="46" height="18" rx="9" fill="#FFD3B0" stroke="#E7A57A" strokeWidth="3" />
          <text x="42" y="68" textAnchor="middle" fontSize="16" fontWeight="900" fill="#B63A12">34°C</text>
          <text x="42" y="125" textAnchor="middle" fontSize="12" fontWeight="800" fill="#6B6887">your hand</text>
        </g>
        {/* metal spoon */}
        <g transform="translate(250 30)">
          <rect x="0" y="12" width="120" height="14" rx="7" fill="url(#metal)" stroke="#8C95A8" strokeWidth="2" />
          <ellipse cx="146" cy="19" rx="30" ry="18" fill="url(#metal)" stroke="#8C95A8" strokeWidth="2" />
          <text x="74" y="50" textAnchor="middle" fontSize="12" fontWeight="800" fill="#6B6887">metal · 25°C · FAST</text>
        </g>
        {/* wooden spoon */}
        <g transform="translate(250 112)">
          <rect x="0" y="12" width="120" height="14" rx="7" fill="url(#wood)" stroke="#8A5427" strokeWidth="2" />
          <ellipse cx="146" cy="19" rx="30" ry="18" fill="url(#wood)" stroke="#8A5427" strokeWidth="2" />
          <text x="74" y="50" textAnchor="middle" fontSize="12" fontWeight="800" fill="#6B6887">wood · 25°C · slow</text>
        </g>
        {/* heat arrows */}
        {[0, 1, 2].map((i) => (
          <motion.path
            key={`m${i}`}
            d={`M140 ${70 + i * 8} C 190 ${60 + i * 4}, 210 ${48 + i * 4}, 244 ${48 + i * 2}`}
            stroke="#FF6B3D"
            strokeWidth={5}
            fill="none"
            strokeLinecap="round"
            strokeDasharray="10 10"
            markerEnd="url(#arrowHead)"
            animate={{ strokeDashoffset: [0, -40] }}
            transition={{ repeat: Infinity, duration: 0.6, ease: "linear" }}
          />
        ))}
        <motion.path
          d="M140 118 C 190 128, 210 138, 244 140"
          stroke="#FFA487"
          strokeWidth={2}
          fill="none"
          strokeLinecap="round"
          strokeDasharray="4 12"
          markerEnd="url(#arrowHead)"
          animate={{ strokeDashoffset: [0, -32] }}
          transition={{ repeat: Infinity, duration: 2.2, ease: "linear" }}
        />
      </svg>
      <p className="mt-1 text-center text-xs font-extrabold text-ink-500">Same temperature — different speed of heat flow.</p>
    </motion.div>
  );
}
