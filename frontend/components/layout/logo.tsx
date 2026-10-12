import Link from "next/link";

import { Curio } from "@/components/mascot/curio";

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/" className="group flex items-center gap-2.5" aria-label="Curio home">
      <div className="grid h-11 w-11 place-items-center rounded-2xl bg-curio-50 ring-1 ring-curio-100 transition group-hover:rotate-[-6deg]">
        <Curio size={34} />
      </div>
      {!compact && (
        <div className="leading-none">
          <div className="text-[22px] font-black tracking-tight text-ink-900">
            curio<span className="text-curio-500">.</span>
          </div>
          <div className="mt-0.5 text-[10px] font-extrabold uppercase tracking-[0.18em] text-ink-400">learn · verify</div>
        </div>
      )}
    </Link>
  );
}
