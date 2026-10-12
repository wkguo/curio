"use client";

import { PageHeader } from "@/components/layout/page-header";
import { SectionTitle } from "@/components/shared/section-title";
import { AnswerVsReasoning } from "@/components/teacher/answer-vs-reasoning";
import { ActivityChart, StrategyChart, TopicDistribution } from "@/components/teacher/charts";
import { MasteryHeatmap } from "@/components/teacher/heatmap";
import { Kpi } from "@/components/teacher/kpi";
import { MisconceptionList } from "@/components/teacher/misconception-list";
import { TraceList } from "@/components/teacher/trace-list";
import { Card } from "@/components/ui/card";
import { Emoji } from "@/components/ui/emoji";
import { Skeleton } from "@/components/ui/skeleton";
import { ReviewQueue } from "@/components/teacher/review-queue";
import { useAnalytics, useTraces } from "@/lib/hooks";
import { CLASSIFICATION, SAFETY_LABEL } from "@/lib/labels";
import type { Classification } from "@/types/api";

export default function TeacherPage() {
  const { data } = useAnalytics();
  const { data: traces } = useTraces(12);

  if (!data) {
    return (
      <div className="mx-auto max-w-7xl space-y-5 px-4 py-8 sm:px-8">
        <Skeleton className="h-16 w-80" />
        <div className="grid gap-4 sm:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-36" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  const topicColor = Object.fromEntries(data.topics.map((t) => [t.topic_id, t.color]));

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow={`Teacher view · ${data.class_name}`}
        title="Class understanding overview"
        subtitle="Curio doesn't just count right answers — it verifies whether students understand why. Here's what that reveals about your class."
      />

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi emoji="busts" label="Students" value={data.students} sub={`${data.active_today} active today`} tint="#EAE4FF" />
        <Kpi emoji="pencil" label="Questions answered" value={data.questions_answered} sub="incl. transfer questions" tint="#D2ECFF" delay={0.05} />
        <Kpi emoji="check_mark_button" label="Verified mastery rate" value={data.verified_mastery_rate * 100} format={(n) => `${Math.round(n)}%`} sub="transfer questions passed" tint="#CFF5E3" delay={0.1} />
        <Kpi emoji="brain" label="Average mastery" value={data.avg_mastery * 100} format={(n) => `${Math.round(n)}%`} sub="across all concepts" tint="#FFEFC2" delay={0.15} />
      </div>

      <Card className="mt-5 p-6">
        <SectionTitle
          emoji={<Emoji name="bell" size={24} />}
          action={<span className="text-xs font-bold text-ink-400">Cases the AI deliberately does not handle alone</span>}
        >
          Needs your attention {data.open_reviews > 0 && <span className="rounded-full bg-coral-500 px-2 py-0.5 text-xs text-white">{data.open_reviews}</span>}
        </SectionTitle>
        <div className="grid gap-5 lg:grid-cols-[1fr_280px]">
          <ReviewQueue limit={5} />
          <div className="space-y-3">
            <div className="rounded-2xl bg-ink-50 p-4">
              <div className="label-caps mb-2">How answers were classified</div>
              <ul className="space-y-1 text-xs font-bold text-ink-600">
                {Object.entries(data.classification_mix)
                  .sort((a, b) => b[1] - a[1])
                  .map(([k, v]) => (
                    <li key={k} className="flex justify-between">
                      <span>{CLASSIFICATION[k as Classification]?.label ?? k}</span>
                      <span className="tabular-nums text-ink-900">{v}</span>
                    </li>
                  ))}
              </ul>
            </div>
            <div className="rounded-2xl bg-ink-50 p-4">
              <div className="label-caps mb-2">Safety layer events</div>
              <ul className="space-y-1 text-xs font-bold text-ink-600">
                {Object.entries(data.safety_events).length === 0 && <li>None</li>}
                {Object.entries(data.safety_events).map(([k, v]) => (
                  <li key={k} className="flex justify-between">
                    <span>{SAFETY_LABEL[k] ?? k}</span>
                    <span className="tabular-nums text-ink-900">{v}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </Card>

      <div className="mt-5 grid gap-5 lg:grid-cols-5">
        <Card className="p-6 lg:col-span-2">
          <SectionTitle emoji={<Emoji name="magnifying_glass" size={24} />}>Right answer ≠ understanding</SectionTitle>
          <AnswerVsReasoning counts={data.answer_vs_reasoning} />
        </Card>
        <Card className="p-6 lg:col-span-3">
          <SectionTitle emoji={<Emoji name="warning" size={24} />}>Top misconceptions</SectionTitle>
          <MisconceptionList items={data.top_misconceptions.slice(0, 6)} topicColor={topicColor} students={data.students} />
        </Card>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2">
          <SectionTitle emoji={<Emoji name="bar_chart" size={24} />}>Learning activity · last 14 days</SectionTitle>
          <ActivityChart data={data.activity} />
        </Card>
        <Card className="p-6">
          <SectionTitle emoji={<Emoji name="books" size={24} />}>Topic mastery</SectionTitle>
          <TopicDistribution data={data.topics} />
        </Card>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-5">
        <Card className="p-6 lg:col-span-3">
          <SectionTitle
            emoji={<Emoji name="microscope" size={24} />}
            action={<span className="text-xs font-bold text-ink-400">Click a row to inspect the full trace</span>}
          >
            AI diagnosis traces
          </SectionTitle>
          {traces ? <TraceList traces={traces} /> : <Skeleton className="h-80" />}
        </Card>
        <Card className="p-6 lg:col-span-2">
          <SectionTitle emoji={<Emoji name="light_bulb" size={24} />}>Which teaching strategies work?</SectionTitle>
          <p className="mb-4 -mt-1 text-xs font-bold text-ink-400">Share of taught interactions later verified by a transfer question.</p>
          <StrategyChart data={data.strategies} />
        </Card>
      </div>

      <Card className="mt-5 p-6">
        <SectionTitle emoji={<Emoji name="puzzle_piece" size={24} />} action={<span className="text-xs font-bold text-ink-400">Sorted: students who need help first</span>}>
          Student × concept mastery
        </SectionTitle>
        <MasteryHeatmap data={data} topicColor={topicColor} />
      </Card>
    </div>
  );
}
