"use client";

import { Cpu, WifiOff, Zap } from "lucide-react";

import { Tooltip } from "@/components/ui/tooltip";
import { useHealth, useOffline } from "@/lib/hooks";
import { cn } from "@/lib/utils";

export function StatusPill({ className }: { className?: string }) {
  const offline = useOffline();
  const { data } = useHealth();
  if (offline) {
    return (
      <Tooltip content="Recorded demo: responses and scores are replayed, not calculated from what you type.">
        <span className={cn("inline-flex items-center gap-1.5 rounded-full bg-sun-100 px-2.5 py-1 text-[11px] font-extrabold text-sun-700", className)}>
          <WifiOff className="h-3.5 w-3.5" /> Recorded demo
        </span>
      </Tooltip>
    );
  }
  if (!data) {
    return <span role="status" className={cn("inline-flex items-center gap-1.5 rounded-full bg-ink-100 px-2.5 py-1 text-[11px] font-extrabold text-ink-500", className)}>Connecting…</span>;
  }
  const llm = data?.llm_available;
  return (
    <Tooltip content={llm ? `Live harness with ${data?.model}` : "Live harness running on curated curriculum rules (deterministic demo mode)."}>
      <span className={cn("inline-flex items-center gap-1.5 rounded-full bg-mint-100 px-2.5 py-1 text-[11px] font-extrabold text-mint-700", className)}>
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-mint-400 opacity-60" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-mint-500" />
        </span>
        {llm ? <Zap className="h-3.5 w-3.5" /> : <Cpu className="h-3.5 w-3.5" />}
        {llm ? "LLM live" : "Rules live"}
      </span>
    </Tooltip>
  );
}
