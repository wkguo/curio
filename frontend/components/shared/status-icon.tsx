import { CheckCircle2, Circle, CircleAlert, Lock } from "lucide-react";

import { STATUS } from "@/lib/labels";
import { cn } from "@/lib/utils";
import type { MasteryStatus } from "@/types/api";

/** Status is never color-alone: icon + (optionally) label. */
export function StatusIcon({ status, className }: { status: MasteryStatus; className?: string }) {
  const c = cn("h-5 w-5 shrink-0", className);
  switch (status) {
    case "mastered":
      return <CheckCircle2 className={cn(c, "text-mint-500")} strokeWidth={2.6} aria-label="Mastered" />;
    case "learning":
      return (
        <svg viewBox="0 0 24 24" className={c} aria-label="Learning">
          <circle cx="12" cy="12" r="9" fill="none" stroke="#F5A70A" strokeWidth="2.6" />
          <path d="M12 3 a9 9 0 0 1 0 18 Z" fill="#F5A70A" />
        </svg>
      );
    case "needs_practice":
      return <CircleAlert className={cn(c, "text-coral-500")} strokeWidth={2.6} aria-label="Needs practice" />;
    case "locked":
      return <Lock className={cn(c, "text-ink-300")} strokeWidth={2.6} aria-label="Locked" />;
    default:
      return <Circle className={cn(c, "text-curio-300")} strokeWidth={2.6} aria-label="Ready to start" />;
  }
}

export function StatusBadge({ status }: { status: MasteryStatus }) {
  const s = STATUS[status];
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-extrabold", s.soft, s.text)}>
      <StatusIcon status={status} className="h-3.5 w-3.5" />
      {s.label}
    </span>
  );
}
