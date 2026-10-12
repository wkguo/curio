"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles, Target } from "lucide-react";
import Link from "next/link";

import { MasteryTrend } from "@/components/dashboard/mastery-trend";
import { Curio } from "@/components/mascot/curio";
import { SectionTitle } from "@/components/shared/section-title";
import { StatusIcon } from "@/components/shared/status-icon";
import { AnimatedNumber } from "@/components/ui/animated-number";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Emoji } from "@/components/ui/emoji";
import { Progress } from "@/components/ui/progress";
import { RichText } from "@/components/ui/rich-text";
import { Ring } from "@/components/ui/ring";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/lib/hooks";
import { STATUS } from "@/lib/labels";
import { cn, pct, timeAgo } from "@/lib/utils";

const fadeUp = { initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 } };

export default function DashboardPage() {
  const { data, isLoading } = useDashboard();

  if (isLoading || !data) {
    return (
      <div className="mx-auto max-w-6xl space-y-5 px-4 py-8 sm:px-8">
        <Skeleton className="h-24" />
        <div className="grid gap-5 lg:grid-cols-3">
          <Skeleton className="h-80 lg:col-span-2" />
          <Skeleton className="h-80" />
        </div>
      </div>
    );
  }

  const { student, current_topic: topic, current_concepts: concepts, today } = data;
  const goalPct = Math.min(1, today.questions_answered / today.goal);

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8 sm:py-8">
      {/* Greeting */}
      <motion.div {...fadeUp} className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="grid h-16 w-16 place-items-center rounded-3xl bg-white shadow-soft ring-1 ring-ink-200/70">
            <Emoji name={student.avatar} size={46} />
          </div>
          <div>
            <h1 className="flex items-center gap-2 text-3xl font-black text-ink-900 sm:text-[34px]">
              Hi {student.display_name}
              <motion.span animate={{ rotate: [0, 18, -8, 18, 0] }} transition={{ duration: 1.4, delay: 0.4 }} className="inline-block origin-[70%_70%]">
                <Emoji name="waving_hand" size={34} />
              </motion.span>
            </h1>
            <p className="text-[15px] font-bold text-ink-500">
              {student.level} · Primary Science · {student.class_name}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          <Stat emoji="fire" value={student.streak_days} label="day streak" tone="bg-coral-50 text-coral-600" />
          <Stat emoji="gem_stone" value={student.xp} label="XP" tone="bg-sky-50 text-sky-700" />
        </div>
      </motion.div>

      <div className="mt-7 grid gap-5 lg:grid-cols-3">
        {/* Continue learning hero */}
        <motion.div {...fadeUp} transition={{ delay: 0.05 }} className="lg:col-span-2">
          <Card className="relative overflow-hidden p-0">
            <div className="absolute inset-0 opacity-90" style={{ background: `linear-gradient(135deg, ${topic.color}22 0%, #fff 55%)` }} />
            <div className="absolute -right-10 -top-10 h-44 w-44 rounded-full opacity-20 blur-2xl" style={{ background: topic.color }} />
            <div className="relative grid gap-6 p-6 sm:grid-cols-[1fr_auto] sm:p-7">
              <div>
                <Badge variant="outline" className="mb-3">
                  <Sparkles /> Current topic
                </Badge>
                <div className="flex items-center gap-3">
                  <Emoji name={topic.emoji} size={52} className="animate-float-y" />
                  <div>
                    <div className="text-sm font-extrabold text-ink-400">Primary Science</div>
                    <h2 className="text-[28px] font-black leading-tight text-ink-900">{topic.name}</h2>
                  </div>
                </div>

                <div className="mt-5">
                  <div className="mb-2 flex items-end justify-between">
                    <span className="text-sm font-extrabold text-ink-500">Mastery</span>
                    <span className="text-3xl font-black tabular-nums" style={{ color: topic.color }}>
                      <AnimatedNumber value={topic.mastery * 100} format={(n) => `${Math.round(n)}%`} />
                    </span>
                  </div>
                  <Progress value={topic.mastery} color={topic.color} height={16} />
                  <div className="mt-2 text-xs font-bold text-ink-400">
                    {topic.mastered} of {topic.total} concepts mastered · {topic.learning} in progress
                  </div>
                </div>

                <div className="mt-6 flex flex-wrap items-center gap-3">
                  <Button asChild size="xl">
                    <Link href={`/learn?topic=${topic.topic_id}`}>
                      Continue Learning <ArrowRight />
                    </Link>
                  </Button>
                  {data.next_up && (
                    <div className="flex items-center gap-2 rounded-2xl bg-white/80 px-3 py-2 text-sm font-bold text-ink-600 ring-1 ring-ink-200">
                      <Target className="h-4 w-4 text-curio-500" />
                      Next: <span className="font-extrabold text-ink-900">{data.next_up.concept_name}</span>
                    </div>
                  )}
                </div>
              </div>

              <ul className="grid content-start gap-1.5 sm:w-60">
                {concepts.map((c, i) => (
                  <motion.li
                    key={c.id}
                    initial={{ opacity: 0, x: 12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.15 + i * 0.05 }}
                    className={cn("flex items-center gap-2.5 rounded-2xl bg-white/85 px-3 py-2 ring-1 ring-ink-200/70", c.status === "locked" && "opacity-60")}
                  >
                    <StatusIcon status={c.status} />
                    <span className="flex-1 truncate text-sm font-extrabold text-ink-800">{c.name}</span>
                    <span className={cn("text-xs font-black tabular-nums", STATUS[c.status].text)}>{c.status === "locked" ? "" : pct(c.mastery)}</span>
                  </motion.li>
                ))}
              </ul>
            </div>
          </Card>
        </motion.div>

        {/* Today */}
        <motion.div {...fadeUp} transition={{ delay: 0.1 }}>
          <Card className="flex h-full flex-col p-6">
            <SectionTitle emoji={<Emoji name="calendar" size={24} />}>Today&apos;s learning</SectionTitle>
            <div className="flex items-center gap-5">
              <Ring value={goalPct} size={112} stroke={12} color="#1FB978" track="#EAFBF3">
                <div className="text-center">
                  <div className="text-3xl font-black text-ink-900">{today.questions_answered}</div>
                  <div className="text-[11px] font-extrabold text-ink-400">of {today.goal} goal</div>
                </div>
              </Ring>
              <div className="space-y-3">
                <MiniStat emoji="check_mark_button" label="Verified" value={today.verified} />
                <MiniStat emoji="gem_stone" label="XP today" value={today.xp_today} />
              </div>
            </div>
            <div className="mt-auto pt-5">
              <div className="rounded-3xl bg-curio-50 p-4">
                <div className="flex items-start gap-3">
                  <Curio size={46} mood="curious" className="shrink-0" />
                  <div>
                    <div className="label-caps !text-curio-500">Curio insight</div>
                    <p className="mt-1 text-sm font-bold leading-snug text-ink-700">
                      <RichText text={data.insight} />
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      </div>

      {/* Topics */}
      <div className="mt-8">
        <SectionTitle emoji={<Emoji name="books" size={24} />} action={<Link href="/progress" className="text-sm font-extrabold text-curio-600 hover:underline">See all progress →</Link>}>
          Your topics
        </SectionTitle>
        <div className="grid gap-4 sm:grid-cols-3">
          {data.topics.map((t, i) => (
            <motion.div key={t.topic_id} {...fadeUp} transition={{ delay: 0.1 + i * 0.06 }}>
              <Link href={`/learn?topic=${t.topic_id}`} className="group block">
                <Card className="relative overflow-hidden p-5 transition group-hover:-translate-y-1 group-hover:shadow-float">
                  <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-15" style={{ background: t.color }} />
                  <div className="relative flex items-center gap-4">
                    <Ring value={t.mastery} size={68} stroke={8} color={t.color}>
                      <Emoji name={t.emoji} size={32} />
                    </Ring>
                    <div className="min-w-0">
                      <div className="truncate text-lg font-black text-ink-900">{t.name}</div>
                      <div className="text-sm font-extrabold" style={{ color: t.color }}>
                        {pct(t.mastery)} mastery
                      </div>
                      <div className="text-xs font-bold text-ink-400">
                        {t.mastered}/{t.total} mastered
                      </div>
                    </div>
                    <ArrowRight className="ml-auto h-5 w-5 text-ink-300 transition group-hover:translate-x-1 group-hover:text-ink-600" />
                  </div>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-5">
        <Card className="p-6 lg:col-span-3">
          <SectionTitle emoji={<Emoji name="chart_increasing" size={24} />}>
            {topic.name} mastery · last 14 days
          </SectionTitle>
          <MasteryTrend data={data.history} color={topic.color} />
        </Card>

        <Card className="p-6 lg:col-span-2">
          <SectionTitle emoji={<Emoji name="sports_medal" size={24} />}>Badges</SectionTitle>
          <div className="grid grid-cols-3 gap-3">
            {data.badges.map((b) => (
              <div
                key={b.id}
                title={b.description}
                className={cn("flex flex-col items-center gap-1.5 rounded-2xl p-3 text-center transition", b.earned ? "bg-sun-50 ring-1 ring-sun-200" : "bg-ink-50 opacity-50 grayscale")}
              >
                <Emoji name={b.emoji} size={34} />
                <span className="text-[11px] font-extrabold leading-tight text-ink-700">{b.name}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent */}
      <Card className="mt-5 p-6">
        <SectionTitle emoji={<Emoji name="hourglass" size={24} />}>Recent activity</SectionTitle>
        {data.recent_activity.length === 0 ? (
          <p className="py-6 text-center font-bold text-ink-400">No activity yet — start your first question!</p>
        ) : (
          <ul className="divide-y divide-ink-100">
            {data.recent_activity.map((a) => (
              <li key={a.id} className="flex items-center gap-4 py-3">
                <div className={cn("grid h-10 w-10 shrink-0 place-items-center rounded-2xl", a.result === "verified" ? "bg-mint-50" : a.result === "learning" ? "bg-sun-50" : "bg-coral-50")}>
                  <Emoji name={a.kind === "transfer" ? "rocket" : a.result === "verified" ? "check_mark_button" : "magnifying_glass"} size={24} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-extrabold text-ink-800">{a.question_prompt}</div>
                  <div className="text-xs font-bold text-ink-400">
                    {a.kind === "transfer" ? "Transfer challenge" : "Question"} · {a.concept_name} · {timeAgo(a.created_at)}
                  </div>
                </div>
                {a.mastery_before != null && a.mastery_after != null && (
                  <div className={cn("shrink-0 text-sm font-black tabular-nums", a.mastery_after >= a.mastery_before ? "text-mint-600" : "text-coral-600")}>
                    {pct(a.mastery_before)} → {pct(a.mastery_after)}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function Stat({ emoji, value, label, tone }: { emoji: string; value: number; label: string; tone: string }) {
  return (
    <div className={cn("flex items-center gap-2 rounded-2xl px-3.5 py-2", tone)}>
      <Emoji name={emoji} size={26} />
      <div className="leading-none">
        <div className="text-lg font-black tabular-nums">
          <AnimatedNumber value={value} />
        </div>
        <div className="text-[10px] font-extrabold uppercase tracking-wider opacity-80">{label}</div>
      </div>
    </div>
  );
}

function MiniStat({ emoji, label, value }: { emoji: string; label: string; value: number }) {
  return (
    <div className="flex items-center gap-2.5">
      <Emoji name={emoji} size={26} />
      <div>
        <div className="text-xl font-black leading-none text-ink-900">{value}</div>
        <div className="text-xs font-bold text-ink-400">{label}</div>
      </div>
    </div>
  );
}
