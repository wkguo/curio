"use client";

import { Emoji } from "@/components/ui/emoji";
import { Tooltip } from "@/components/ui/tooltip";
import type { ClassAnalytics } from "@/types/api";

// Sequential single-hue ramp (violet), light → dark.
const RAMP = ["#F3F2F8", "#EAE4FF", "#D6CBFF", "#B8A6FF", "#9A80FF", "#7C5CFF", "#5631D6"];
const cell = (v: number) => RAMP[Math.min(RAMP.length - 1, Math.floor(v * (RAMP.length - 0.001)))];

export function MasteryHeatmap({ data, topicColor }: { data: ClassAnalytics; topicColor: Record<string, string> }) {
  const concepts = data.heatmap_concepts;
  return (
    <div className="scroll-thin overflow-x-auto">
      <table className="border-separate border-spacing-[3px]">
        <thead>
          <tr>
            <th />
            {concepts.map((c) => (
              <th key={c.id} className="h-28 w-7 align-bottom">
                <div className="flex h-full items-end justify-center">
                  <span className="whitespace-nowrap text-[10px] font-extrabold text-ink-500 [writing-mode:vertical-rl] rotate-180">{c.name}</span>
                </div>
                <div className="mx-auto mt-1 h-1 w-5 rounded-full" style={{ background: topicColor[c.topic_id] }} />
              </th>
            ))}
            <th className="pl-2 text-left align-bottom text-[10px] font-extrabold uppercase text-ink-400">Avg</th>
          </tr>
        </thead>
        <tbody>
          {data.roster.map((s) => (
            <tr key={s.id}>
              <td className="pr-2">
                <div className="flex items-center gap-1.5 whitespace-nowrap text-xs font-extrabold text-ink-700">
                  <Emoji name={s.avatar} size={18} /> {s.display_name}
                </div>
              </td>
              {concepts.map((c) => {
                const v = s.scores[c.id] ?? 0;
                return (
                  <td key={c.id} className="p-0">
                    <Tooltip content={`${s.display_name} · ${c.name}: ${Math.round(v * 100)}%`}>
                      <div className="h-6 w-7 cursor-help rounded-md transition hover:scale-125 hover:ring-2 hover:ring-ink-900/20" style={{ background: cell(v) }} />
                    </Tooltip>
                  </td>
                );
              })}
              <td className="pl-2 text-xs font-black tabular-nums text-ink-700">{Math.round(s.avg_mastery * 100)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-3 flex items-center gap-2 text-[11px] font-bold text-ink-400">
        0%
        <div className="flex">
          {RAMP.map((c) => (
            <span key={c} className="h-2.5 w-6" style={{ background: c }} />
          ))}
        </div>
        100% mastery
      </div>
    </div>
  );
}
