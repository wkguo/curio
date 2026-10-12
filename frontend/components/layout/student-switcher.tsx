"use client";

import { ChevronsUpDown, RotateCcw } from "lucide-react";
import { useState } from "react";

import { Emoji } from "@/components/ui/emoji";
import { useStudents } from "@/lib/hooks";
import { useStudent } from "@/lib/student-context";
import { cn } from "@/lib/utils";

export function StudentSwitcher() {
  const { studentId, setStudentId, resetDemo } = useStudent();
  const { data: students } = useStudents();
  const [open, setOpen] = useState(false);
  const [resetting, setResetting] = useState(false);
  const me = students?.find((s) => s.id === studentId) ?? students?.[0];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 rounded-2xl border-2 border-ink-100 bg-white p-2.5 text-left transition hover:border-curio-200"
        aria-expanded={open}
      >
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-sun-50">
          <Emoji name={me?.avatar ?? "fox"} size={30} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-extrabold text-ink-900">{me?.display_name ?? "Alex"}</div>
          <div className="truncate text-xs font-bold text-ink-400">
            {me?.level ?? "Primary 5"} · {me?.is_demo ? "demo student" : me?.class_name}
          </div>
        </div>
        <ChevronsUpDown className="h-4 w-4 text-ink-400" />
      </button>

      {open && (
        <div className="absolute bottom-full left-0 z-40 mb-2 w-full overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-float">
          <div className="label-caps px-3 pb-1 pt-3">View as student</div>
          <div className="scroll-thin max-h-64 overflow-y-auto p-1.5">
            {students?.map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setStudentId(s.id);
                  setOpen(false);
                }}
                className={cn(
                  "flex w-full items-center gap-2.5 rounded-xl px-2 py-1.5 text-left text-sm font-bold text-ink-700 hover:bg-curio-50",
                  s.id === studentId && "bg-curio-50 text-curio-700",
                )}
              >
                <Emoji name={s.avatar} size={22} />
                <span className="flex-1 truncate">{s.display_name}</span>
                {s.is_demo && <span className="rounded-full bg-curio-100 px-1.5 text-[10px] font-extrabold text-curio-700">DEMO</span>}
              </button>
            ))}
          </div>
          <button
            onClick={async () => {
              setResetting(true);
              await resetDemo();
              setResetting(false);
              setOpen(false);
            }}
            className="flex w-full items-center justify-center gap-2 border-t border-ink-100 px-3 py-2.5 text-sm font-extrabold text-coral-600 hover:bg-coral-50"
          >
            <RotateCcw className={cn("h-4 w-4", resetting && "animate-spin")} /> Reset demo (Alex)
          </button>
        </div>
      )}
    </div>
  );
}
