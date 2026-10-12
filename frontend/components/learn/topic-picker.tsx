"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { CurioSays } from "@/components/mascot/curio";
import { Emoji } from "@/components/ui/emoji";
import { Ring } from "@/components/ui/ring";
import { Skeleton } from "@/components/ui/skeleton";
import { useTopics } from "@/lib/hooks";
import { pct } from "@/lib/utils";

export function TopicPicker({ onPick }: { onPick: (topicId: string) => void }) {
  const { data } = useTopics();
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-8">
      <PageHeader eyebrow="Learn" title="What shall we explore today?" subtitle="Pick a topic. Curio will ask you questions, check your reasoning, and help you really understand." />
      <div className="mt-6">
        <CurioSays mood="wave">
          Remember: I care about <span className="text-curio-600">why</span>, not just the answer. Explain your thinking! 💭
        </CurioSays>
      </div>
      <div className="mt-8 grid gap-5 md:grid-cols-3">
        {!data && [0, 1, 2].map((i) => <Skeleton key={i} className="h-72" />)}
        {data?.map((t, i) => (
          <motion.button
            key={t.topic_id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            whileHover={{ y: -6 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onPick(t.topic_id)}
            className="group card-base relative overflow-hidden p-6 text-left"
          >
            <div className="absolute inset-x-0 top-0 h-28 opacity-90" style={{ background: `linear-gradient(180deg, ${t.color}26, transparent)` }} />
            <div className="relative">
              <div className="flex items-start justify-between">
                <Emoji name={t.emoji} size={72} className="transition group-hover:rotate-[-8deg] group-hover:scale-110" />
                {t.mastery != null && (
                  <Ring value={t.mastery} size={54} stroke={6} color={t.color}>
                    <span className="text-xs font-black text-ink-700">{pct(t.mastery)}</span>
                  </Ring>
                )}
              </div>
              <h3 className="mt-4 text-2xl font-black text-ink-900">{t.name}</h3>
              <p className="mt-1 text-sm font-bold" style={{ color: t.color }}>
                {t.tagline}
              </p>
              <p className="mt-3 line-clamp-3 text-sm font-semibold text-ink-500">{t.description}</p>
              <div className="mt-5 flex items-center justify-between text-xs font-extrabold text-ink-400">
                <span>
                  {t.concept_count} concepts · {t.question_count} questions
                </span>
                <span className="grid h-9 w-9 place-items-center rounded-full bg-ink-900 text-white transition group-hover:translate-x-1">
                  <ArrowRight className="h-4 w-4" />
                </span>
              </div>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
