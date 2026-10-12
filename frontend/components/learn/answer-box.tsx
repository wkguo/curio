"use client";

import { CornerDownLeft, Wand2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export interface DemoChip {
  label: string;
  text: string;
}

/** Answer input with Ctrl/⌘+Enter submit and optional demo shortcuts. */
export function AnswerBox({
  value,
  onChange,
  onSubmit,
  busy,
  placeholder,
  cta,
  demo = [],
  rows = 3,
  variant = "default",
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  busy?: boolean;
  placeholder: string;
  cta: string;
  demo?: DemoChip[];
  rows?: number;
  variant?: "default" | "mint" | "sun";
}) {
  const disabled = busy || value.trim().length < 2;
  return (
    <div className="space-y-3">
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        maxLength={600}
        disabled={busy}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && !disabled) onSubmit();
        }}
      />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {demo.length > 0 && (
            <>
              <span className="inline-flex items-center gap-1 text-[11px] font-extrabold uppercase tracking-wider text-ink-400">
                <Wand2 className="h-3.5 w-3.5" /> Demo
              </span>
              {demo.map((d) => (
                <button
                  key={d.label}
                  type="button"
                  onClick={() => onChange(d.text)}
                  disabled={busy}
                  className="rounded-full border border-dashed border-curio-300 bg-curio-50/60 px-3 py-1 text-xs font-extrabold text-curio-700 transition hover:bg-curio-100"
                >
                  {d.label}
                </button>
              ))}
            </>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden items-center gap-1 text-xs font-bold text-ink-300 sm:flex">
            Ctrl <CornerDownLeft className="h-3 w-3" />
          </span>
          <Button onClick={onSubmit} disabled={disabled} variant={variant} size="lg">
            {cta}
          </Button>
        </div>
      </div>
    </div>
  );
}
