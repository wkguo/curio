"use client";

import { motion } from "framer-motion";
import { Check, RefreshCw, X } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { StatusBadge } from "@/components/shared/status-icon";
import { Card } from "@/components/ui/card";
import { Emoji } from "@/components/ui/emoji";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTopic, useTopics } from "@/lib/hooks";
import { MISCONCEPTION_TYPE } from "@/lib/labels";
import type { MisconceptionCard } from "@/types/api";

export default function ConceptsPage() {
  const { data: topics } = useTopics();
  const [topicId, setTopicId] = useState("heat_transfer");
  const { data: topic } = useTopic(topicId);

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="Concepts"
        title="Concept library"
        subtitle="The big ideas in each topic — and the sneaky myths Curio helps you bust."
        actions={
          <Tabs value={topicId} onValueChange={setTopicId}>
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

      <section className="mt-8">
        <h2 className="mb-1 flex items-center gap-2 text-xl font-black text-ink-900">
          <Emoji name="magnifying_glass" size={26} /> Myth busters
        </h2>
        <p className="mb-4 text-sm font-bold text-ink-400">Tap a card to flip it from myth to fact.</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {!topic && [0, 1, 2].map((i) => <Skeleton key={i} className="h-52" />)}
          {topic?.misconceptions.map((m, i) => <MythCard key={m.id} m={m} delay={i * 0.05} conceptName={topic.concepts.find((c) => c.id === m.concept)?.name ?? ""} />)}
        </div>
      </section>

      <section className="mt-10">
        <h2 className="mb-4 flex items-center gap-2 text-xl font-black text-ink-900">
          <Emoji name="light_bulb" size={26} /> Big ideas
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          {topic?.concepts.map((c, i) => (
            <motion.div key={c.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
              <Card className="h-full p-5">
                <div className="flex items-start gap-4">
                  <div className="grid h-16 w-16 shrink-0 place-items-center rounded-2xl" style={{ background: `${topic.color}14` }}>
                    <Emoji name={c.emoji} size={42} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-lg font-black text-ink-900">{c.name}</h3>
                      <StatusBadge status={c.status} />
                    </div>
                    <p className="mt-1 text-sm font-bold text-ink-500">{c.summary}</p>
                  </div>
                </div>
                <ul className="mt-4 space-y-2">
                  {c.key_ideas.map((k) => (
                    <li key={k} className="flex items-start gap-2 text-sm font-semibold text-ink-700">
                      <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-mint-100">
                        <Check className="h-3 w-3 text-mint-600" strokeWidth={3.5} />
                      </span>
                      {k}
                    </li>
                  ))}
                </ul>
                {c.prerequisites.length > 0 && (
                  <div className="mt-4 text-xs font-bold text-ink-400">
                    Builds on:{" "}
                    {c.prerequisites.map((p) => topic.concepts.find((x) => x.id === p)?.name ?? p).join(", ")}
                  </div>
                )}
              </Card>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}

function MythCard({ m, conceptName, delay }: { m: MisconceptionCard; conceptName: string; delay: number }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <motion.button
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      onClick={() => setFlipped((f) => !f)}
      className="group relative h-56 w-full text-left [perspective:1200px]"
      aria-label={flipped ? `Fact: ${m.corrective_target}` : `Myth: ${m.statement}`}
    >
      <motion.div animate={{ rotateY: flipped ? 180 : 0 }} transition={{ type: "spring", stiffness: 160, damping: 18 }} className="relative h-full w-full [transform-style:preserve-3d]">
        {/* Myth */}
        <div className="absolute inset-0 flex flex-col rounded-3xl border-2 border-coral-200 bg-gradient-to-br from-coral-50 to-white p-5 shadow-soft [backface-visibility:hidden]">
          <div className="flex items-center justify-between">
            <span className="inline-flex items-center gap-1 rounded-full bg-coral-500 px-2.5 py-1 text-[11px] font-extrabold text-white">
              <X className="h-3.5 w-3.5" strokeWidth={3} /> MYTH
            </span>
            <span className="text-[11px] font-extrabold text-coral-600">{MISCONCEPTION_TYPE[m.type]}</span>
          </div>
          <p className="mt-4 text-lg font-black leading-snug text-ink-900">“{m.statement}”</p>
          <div className="mt-auto flex items-center justify-between text-xs font-extrabold text-ink-400">
            <span>{conceptName}</span>
            <span className="inline-flex items-center gap-1 text-curio-600 group-hover:underline">
              <RefreshCw className="h-3.5 w-3.5" /> Flip
            </span>
          </div>
        </div>
        {/* Fact */}
        <div className="absolute inset-0 flex flex-col rounded-3xl border-2 border-mint-200 bg-gradient-to-br from-mint-50 to-white p-5 shadow-soft [backface-visibility:hidden] [transform:rotateY(180deg)]">
          <span className="inline-flex w-fit items-center gap-1 rounded-full bg-mint-500 px-2.5 py-1 text-[11px] font-extrabold text-white">
            <Check className="h-3.5 w-3.5" strokeWidth={3} /> FACT
          </span>
          <p className="mt-4 text-[15px] font-extrabold leading-snug text-ink-800">{m.corrective_target}</p>
          <div className="mt-auto text-xs font-extrabold text-mint-700">{m.label} — busted!</div>
        </div>
      </motion.div>
    </motion.button>
  );
}
