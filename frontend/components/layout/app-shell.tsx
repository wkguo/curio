"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "@/components/layout/logo";
import { STUDENT_NAV, TEACHER_NAV, type NavItem } from "@/components/layout/nav";
import { StatusPill } from "@/components/layout/status-pill";
import { StudentSwitcher } from "@/components/layout/student-switcher";
import { cn } from "@/lib/utils";

function NavLink({ item, active }: { item: NavItem; active: boolean }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      className={cn(
        "group flex items-center gap-3 rounded-2xl px-3 py-2.5 text-[15px] font-extrabold transition-all",
        active ? "bg-curio-50 text-curio-700 ring-2 ring-curio-100" : "text-ink-500 hover:bg-ink-50 hover:text-ink-800",
      )}
    >
      <span className={cn("grid h-9 w-9 place-items-center rounded-xl transition", active ? "bg-white shadow-soft" : "bg-ink-50 group-hover:bg-white")}>
        <Icon className={cn("h-[18px] w-[18px]", item.color)} strokeWidth={2.5} />
      </span>
      {item.label}
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const all = [...STUDENT_NAV, ...TEACHER_NAV].map((n) => n.href);
  // longest matching prefix wins, so /teacher/content doesn't also light up /teacher
  const best = all.filter((h) => path === h || path.startsWith(`${h}/`)).sort((a, b) => b.length - a.length)[0];
  const isActive = (href: string) => href === best;

  return (
    <div className="paper-bg min-h-screen">
      {/* Sidebar (desktop) */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[264px] flex-col border-r border-ink-200/70 bg-white/85 px-4 pb-4 pt-5 backdrop-blur-xl lg:flex">
        <div className="px-1">
          <Logo />
        </div>
        <nav className="mt-8 flex flex-1 flex-col gap-1.5">
          <div className="label-caps px-3 pb-1">Student</div>
          {STUDENT_NAV.map((item) => (
            <NavLink key={item.href} item={item} active={isActive(item.href)} />
          ))}
          <div className="label-caps px-3 pb-1 pt-6">Teacher view</div>
          {TEACHER_NAV.map((item) => (
            <NavLink key={item.href} item={item} active={isActive(item.href)} />
          ))}
        </nav>
        <div className="space-y-3">
          <div className="flex justify-center">
            <StatusPill />
          </div>
          <StudentSwitcher />
        </div>
      </aside>

      {/* Top bar (mobile) */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-ink-200/70 bg-white/85 px-4 py-2.5 backdrop-blur-xl lg:hidden">
        <Logo />
        <StatusPill />
      </header>

      <main className="pb-28 lg:pb-10 lg:pl-[264px]">{children}</main>

      {/* Bottom tabs (mobile) */}
      <nav className="fixed inset-x-3 bottom-3 z-30 flex items-center justify-around rounded-3xl border border-ink-200 bg-white/95 p-1.5 shadow-float backdrop-blur-xl lg:hidden">
        {[...STUDENT_NAV.slice(0, 4), TEACHER_NAV[0]].map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn("flex flex-1 flex-col items-center gap-0.5 rounded-2xl py-1.5 text-[10px] font-extrabold", active ? "bg-curio-50 text-curio-700" : "text-ink-400")}
            >
              <Icon className={cn("h-5 w-5", active && item.color)} strokeWidth={2.5} />
              {item.label.split(" ")[0]}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
