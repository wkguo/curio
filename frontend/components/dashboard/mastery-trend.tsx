"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { shortDate } from "@/lib/utils";

/** Single-series area: topic mastery over the last 14 days. Title names the series (no legend). */
export function MasteryTrend({ data, color = "#7C5CFF" }: { data: { date: string; mastery: number; answers: number }[]; color?: string }) {
  const rows = data.map((d) => ({ ...d, pct: Math.round(d.mastery * 100), label: shortDate(d.date) }));
  return (
    <div className="h-[190px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
          <defs>
            <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.28} />
              <stop offset="100%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="#EFEEF5" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#9A97B0", fontSize: 11, fontWeight: 700 }} interval={3} />
          <YAxis domain={[0, 100]} ticks={[0, 50, 100]} tickLine={false} axisLine={false} tick={{ fill: "#9A97B0", fontSize: 11, fontWeight: 700 }} unit="%" />
          <Tooltip
            cursor={{ stroke: color, strokeWidth: 1, strokeDasharray: "4 4" }}
            content={({ active, payload }) =>
              active && payload?.length ? (
                <div className="rounded-xl bg-ink-900 px-3 py-2 text-xs font-bold text-white shadow-float">
                  <div className="text-ink-300">{payload[0].payload.label}</div>
                  <div>
                    Mastery <span className="text-base font-black">{payload[0].payload.pct}%</span>
                  </div>
                  <div className="text-ink-300">{payload[0].payload.answers} learning events</div>
                </div>
              ) : null
            }
          />
          <Area type="monotone" dataKey="pct" stroke={color} strokeWidth={2.5} fill="url(#trendFill)" activeDot={{ r: 5, strokeWidth: 2, stroke: "#fff" }} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
