"use client";

import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from "recharts";

import type { ConceptNode } from "@/types/api";

/** One series (this student's mastery per concept) → no legend; the card title names it. */
export function TopicRadar({ concepts, color }: { concepts: ConceptNode[]; color: string }) {
  const data = concepts.map((c) => ({ name: c.name.length > 14 ? `${c.name.slice(0, 13)}…` : c.name, full: c.name, v: Math.round(c.mastery * 100) }));
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="72%">
          <PolarGrid stroke="#E6E4EF" />
          <PolarAngleAxis dataKey="name" tick={{ fill: "#55516F", fontSize: 11, fontWeight: 800 }} />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
          <Tooltip
            content={({ active, payload }) =>
              active && payload?.length ? (
                <div className="rounded-xl bg-ink-900 px-3 py-2 text-xs font-bold text-white">
                  {payload[0].payload.full}: <b>{payload[0].payload.v}%</b>
                </div>
              ) : null
            }
          />
          <Radar dataKey="v" stroke={color} strokeWidth={2} fill={color} fillOpacity={0.22} dot={{ r: 3.5, fill: color, strokeWidth: 0 }} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
