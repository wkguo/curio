"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { STRATEGY } from "@/lib/labels";
import { shortDate } from "@/lib/utils";
import type { ClassAnalytics } from "@/types/api";

const axis = { fill: "#9A97B0", fontSize: 11, fontWeight: 700 };

function Tip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl bg-ink-900 px-3 py-2 text-xs font-bold text-white shadow-float">
      <div className="mb-1 text-ink-300">{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: p.color }} />
          {p.name}: <b>{p.value}</b>
        </div>
      ))}
    </div>
  );
}

/** Two series (answers vs verified) — validated violet/mint pair, legend + tooltip. */
export function ActivityChart({ data }: { data: ClassAnalytics["activity"] }) {
  const rows = data.map((d) => ({ ...d, label: shortDate(d.date) }));
  return (
    <div className="h-[230px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 8, right: 4, left: -20, bottom: 0 }} barGap={2}>
          <CartesianGrid vertical={false} stroke="#EFEEF5" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} tick={axis} interval={2} />
          <YAxis tickLine={false} axisLine={false} tick={axis} allowDecimals={false} />
          <Tooltip content={<Tip />} cursor={{ fill: "#F4F1FF" }} />
          <Legend iconType="circle" iconSize={9} wrapperStyle={{ fontSize: 12, fontWeight: 800, color: "#55516F" }} />
          <Bar dataKey="answers" name="Answers" fill="#7C5CFF" radius={[4, 4, 0, 0]} maxBarSize={14} />
          <Bar dataKey="verified" name="Verified by transfer" fill="#1FB978" radius={[4, 4, 0, 0]} maxBarSize={14} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Magnitude per strategy — single hue, direct value labels. */
export function StrategyChart({ data }: { data: ClassAnalytics["strategies"] }) {
  const rows = data.map((s) => ({ name: STRATEGY[s.strategy]?.label ?? s.strategy, rate: Math.round(s.success_rate * 100), uses: s.uses }));
  return (
    <div className="space-y-2.5">
      {rows.map((r) => (
        <div key={r.name}>
          <div className="mb-1 flex justify-between text-xs font-extrabold text-ink-600">
            <span>{r.name}</span>
            <span className="tabular-nums text-ink-400">
              <b className="text-ink-800">{r.rate}%</b> verified · {r.uses} uses
            </span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-ink-100">
            <div className="h-full rounded-full bg-curio-500 transition-all duration-700" style={{ width: `${r.rate}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Status distribution per topic (reserved status colors, with legend). */
export function TopicDistribution({ data }: { data: ClassAnalytics["topics"] }) {
  return (
    <div className="space-y-4">
      {data.map((t) => {
        const total = t.mastered + t.learning + t.needs_practice || 1;
        const segs = [
          { k: "Mastered", v: t.mastered, c: "#1FB978" },
          { k: "Learning", v: t.learning, c: "#F5A70A" },
          { k: "Needs practice", v: t.needs_practice, c: "#FF6B3D" },
        ];
        return (
          <div key={t.topic_id}>
            <div className="mb-1.5 flex items-center justify-between text-sm font-extrabold text-ink-800">
              <span>{t.name}</span>
              <span className="text-ink-400">avg {Math.round(t.avg_mastery * 100)}%</span>
            </div>
            <div className="flex h-3.5 gap-[2px] overflow-hidden rounded-full">
              {segs.map((s) => (
                <div key={s.k} title={`${s.k}: ${s.v}`} style={{ width: `${(s.v / total) * 100}%`, background: s.c }} />
              ))}
            </div>
          </div>
        );
      })}
      <div className="flex flex-wrap gap-3 pt-1 text-xs font-bold text-ink-500">
        {[
          ["Mastered", "#1FB978"],
          ["Learning", "#F5A70A"],
          ["Needs practice", "#FF6B3D"],
        ].map(([k, c]) => (
          <span key={k} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: c }} /> {k}
          </span>
        ))}
      </div>
    </div>
  );
}
