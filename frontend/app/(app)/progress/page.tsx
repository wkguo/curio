"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Target } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { ConceptGraph } from "@/components/progress/concept-graph";
import { TopicRadar } from "@/components/progress/topic-radar";
import { ConceptBar } from "@/components/shared/concept-bar";
import { StatusBadge, StatusIcon } from "@/components/shared/status-icon";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Emoji } from "@/components/ui/emoji";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTopic, useTopics } from "@/lib/hooks";
import { STATUS } from "@/lib/labels";
import { pct } from "@/lib/utils";
import type { MasteryStatus } from "@/types/api";

export default function ProgressPage() {
  const { data: topics } = useTopics();
  const [topicId, setTopicId] = useState("heat_transfer");
  const { data: topic } = useTopic(topicId);
  const [selected, setSelected] = useState<string | undefined>();
  const concept = topic?.concepts.find((c) => c.id === selected) ?? topic?.concepts.find((c) => c.status === "learning") ?? topic?.concepts[0];

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="Progress"
        title="Your concept map"
        subtitle="Every concept you've verified — and what unlocks next. A concept is only marked mastered after you explain why AND pass a question back in a new situation."
        actions={
          <Tabs value={topicId} onValueChange={(v) => { setTopicId(v); setSelected(undefined); }}>
            <TabsList>
              {topics?.map((t) => (
                <TabsTrigger key={t.topic_id} value={t.topic_id}>
                  <Emoji name={t.emoji} size={20} /> {t.name}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        }
      />

      <div className="mt-4 flex flex-wrap gap-2">
        {(Object.keys(STATUS) as MasteryStatus[]).map((s) => (
          <span key={s} className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-xs font-extrabold text-ink-600 ring-1 ring-ink-200">
            <StatusIcon status={s} className="h-4 w-4" /> {STATUS[s].label}
          </span>
        ))}
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Card className="p-2">{topic ? <ConceptGraph concepts={topic.concepts} edges={topic.edges} selected={concept?.id} onSelect={setSelected} /> : <Skeleton className="h-[560px]" />}</Card>

        <AnimatePresence mode="wait">
          {concept && (
            <motion.div key={concept.id} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }}>
              <Card className="h-full p-6">
                <div className="flex items-start justify-between">
                  <Emoji name={concept.emoji} size={60} />
                  <StatusBadge status={concept.status} />
                </div>
                <h2 className="mt-3 text-2xl font-black text-ink-900">{concept.name}</h2>
                <p className="mt-1 text-sm font-bold text-ink-500">{concept.summary}</p>
                <div className="mt-4 rounded-2xl bg-ink-50 p-3">
                  <div className="label-caps mb-1 flex items-center gap-1">
                    <Target className="h-3.5 w-3.5" /> Learning goal
                  </div>
                  <p className="text-sm font-bold text-ink-700">{concept.learning_objective}</p>
                </div>
                {concept.mastery_criterion && (
                  <div className="mt-3 rounded-2xl bg-mint-50 p-3">
                    <div className="label-caps mb-1 !text-mint-700">Mastery criterion</div>
                    <p className="text-sm font-bold text-ink-700">{concept.mastery_criterion}</p>
                  </div>
                )}
                <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                  <Mini label="Mastery" value={pct(concept.mastery)} />
                  <Mini label="Attempts" value={String(concept.attempts)} />
                  <Mini label="Verified" value={String(concept.verified)} />
                </div>
                {concept.misconceptions.length > 0 && (
                  <div className="mt-4">
                    <div className="label-caps mb-1.5">Watch out for</div>
                    <div className="flex flex-wrap gap-1.5">
                      {concept.misconceptions.map((m) => (
                        <span key={m} className="rounded-full bg-coral-50 px-2.5 py-1 text-xs font-extrabold text-coral-700">
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {concept.status !== "locked" && (
                  <Button asChild className="mt-6 w-full" size="lg">
                    <Link href={`/learn?topic=${topicId}`}>
                      Practise this <ArrowRight />
                    </Link>
                  </Button>
                )}
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Card className="p-6">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-black text-ink-900">
            <Emoji name={topic?.emoji ?? "fire"} size={24} /> {topic?.name} · mastery by concept
          </h2>
          <div className="space-y-1">
            {topic?.concepts.map((c, i) => <ConceptBar key={c.id} concept={c} delay={i * 0.06} highlight={c.id === concept?.id} />)}
          </div>
        </Card>
        <Card className="p-6">
          <h2 className="mb-1 flex items-center gap-2 text-lg font-black text-ink-900">
            <Emoji name="direct_hit" size={24} /> Mastery shape
          </h2>
          <p className="text-sm font-semibold text-ink-400">Your mastery per concept (0–100%).</p>
          {topic && <TopicRadar concepts={topic.concepts} color={topic.color} />}
        </Card>
      </div>
    </div>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white p-2 ring-1 ring-ink-200">
      <div className="text-lg font-black text-ink-900">{value}</div>
      <div className="text-[10px] font-extrabold uppercase tracking-wider text-ink-400">{label}</div>
    </div>
  );
}
