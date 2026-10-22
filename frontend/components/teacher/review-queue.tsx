"use client";

import { Check, HeartHandshake, HelpCircle, LifeBuoy, RotateCcw } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Emoji } from "@/components/ui/emoji";
import { api } from "@/lib/api";
import { useQueue } from "@/lib/hooks";
import { SAFETY_LABEL } from "@/lib/labels";
import { cn, timeAgo } from "@/lib/utils";
import type { ReviewItem } from "@/types/api";

const KIND: Record<ReviewItem["kind"], { label: string; icon: typeof Check; tone: string }> = {
  safety: { label: "Safety flag", icon: HeartHandshake, tone: "bg-coral-50 text-coral-700" },
  deferred: { label: "Deferred — AI unsure", icon: HelpCircle, tone: "bg-sky-50 text-sky-700" },
  persistent_misconception: { label: "Persistent misconception", icon: RotateCcw, tone: "bg-sun-50 text-sun-700" },
  stuck: { label: "Stuck — kept saying “I don't know”", icon: LifeBuoy, tone: "bg-sky-50 text-sky-700" },
};

/** Cases the AI deliberately does not handle alone (proposal: defer to teacher review). */
export function ReviewQueue({ limit }: { limit?: number }) {
  const { data, mutate } = useQueue();
  const [busy, setBusy] = useState<string | null>(null);
  if (!data) return <div className="h-24 animate-pulse rounded-2xl bg-ink-100" />;
  if (data.length === 0)
    return (
      <div className="flex items-center gap-3 rounded-2xl bg-mint-50 p-4 text-sm font-bold text-mint-700">
        <Emoji name="check_mark_button" size={24} /> Nothing needs your attention right now.
      </div>
    );
  return (
    <ul className="space-y-2">
      {data.slice(0, limit ?? data.length).map((it) => {
        const k = KIND[it.kind];
        const Icon = k.icon;
        return (
          <li key={it.id} className="flex items-start gap-3 rounded-2xl border border-ink-200 bg-white p-3">
            <span className={cn("mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl", k.tone)}>
              <Icon className="h-4 w-4" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2 text-sm font-extrabold text-ink-900">
                <Emoji name={it.avatar} size={18} /> {it.student_name}
                <span className={cn("rounded-full px-2 py-0.5 text-[10px]", k.tone)}>{k.label}</span>
                {it.kind === "safety" && <span className="text-[11px] font-bold text-ink-400">{SAFETY_LABEL[it.category] ?? it.category}</span>}
                {it.severity === "high" && <span className="rounded-full bg-coral-500 px-2 py-0.5 text-[10px] text-white">HIGH</span>}
              </div>
              <div className="mt-0.5 truncate text-xs font-semibold italic text-ink-500">“{it.excerpt}”</div>
              <div className="text-[11px] font-bold text-ink-400">
                {it.question_prompt ? `${it.question_prompt.slice(0, 70)}… · ` : ""}
                {timeAgo(it.created_at)}
              </div>
            </div>
            <Button
              size="sm"
              variant="secondary"
              disabled={busy === it.id}
              onClick={async () => {
                setBusy(it.id);
                await api.resolveQueue(it.id, "Followed up with student");
                await mutate();
                setBusy(null);
              }}
            >
              <Check /> Resolve
            </Button>
          </li>
        );
      })}
    </ul>
  );
}
