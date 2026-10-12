import { BookOpenCheck, ClipboardCheck, FlaskConical, LayoutDashboard, Lightbulb, Presentation, ShieldCheck, TrendingUp, type LucideIcon } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  color: string;
}

export const STUDENT_NAV: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, color: "text-curio-500" },
  { href: "/learn", label: "Learn", icon: BookOpenCheck, color: "text-coral-500" },
  { href: "/progress", label: "Progress", icon: TrendingUp, color: "text-mint-500" },
  { href: "/concepts", label: "Concepts", icon: Lightbulb, color: "text-sun-500" },
  { href: "/privacy", label: "Privacy", icon: ShieldCheck, color: "text-sky-500" },
];

export const TEACHER_NAV: NavItem[] = [
  { href: "/teacher", label: "Class insights", icon: Presentation, color: "text-sky-500" },
  { href: "/teacher/content", label: "Content review", icon: ClipboardCheck, color: "text-mint-500" },
  { href: "/teacher/evaluation", label: "Evaluation", icon: FlaskConical, color: "text-curio-500" },
];
