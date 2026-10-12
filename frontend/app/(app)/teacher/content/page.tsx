"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown, Flag, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Emoji } from "@/components/ui/emoji";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { usePathways, useTopics } from "@/lib/hooks";
import { cn } from "@/lib/utils";
import type { Pathway } from "@/types/api";

const STATUS = {
  draft: { label: "Draft", tone: "bg-ink-100 text-ink-600" },
  approved: { label: "Approved", tone: "bg-mint-100 text-mint-700" },
  flagged: { label: "Flagged", tone: "bg-coral-100 text-coral-700" },
};

export default function ContentReviewPage() {
  const { data: topics } = useTopics();
  const [topicId, setTopicId] = useState("heat_transfer");
  const { data, mutate } = usePathways();
  const shown = data?.filter((p) => p.topic_id === topicId);
  const counts = { draft: 0, approved: 0, flagged: 0 };
  data?.forEach((p) => (counts[p.review_status] += 1));

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="Teacher view · content"
        title="Concept pathway review"
        subtitle="Every pathway the AI uses — learning objective, expected explanation, misconceptions, diagnostic question, follow-up questions and mastery criterion — for a teacher to approve before use."
      />
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <div className="flex gap-2">
          {(Object.keys(STATUS) as (keyof typeof STATUS)[]).map((k) => (
            <span key={k} className={cn("rounded-full px-3 py-1 text-xs font-extrabold", STATUS[k].tone)}>
              {counts[k]} {STATUS[k].label.toLowerCase()}
            </span>
          ))}
        </div>
        <span className="text-xs font-bold text-ink-400">
          Set <code className="rounded bg-ink-100 px-1">CURIO_REQUIRE_REVIEWED_CONTENT=true</code> to serve only approved pathways to students.
        </span>
        <Tabs value={topicId} onValueChange={setTopicId} className="ml-auto">
          <TabsList>
            {topics?.map((t) => (
              <TabsTrigger key={t.topic_id} value={t.topic_id}>
                <Emoji name={t.emoji} size={18} /> {t.name}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>
      <div className="mt-5 space-y-3">
        {!shown && [0, 1, 2].map((i) => <Skeleton key={i} className="h-20" />)}
        {shown?.map((p) => <PathwayCard key={p.id} p={p} onSaved={() => mutate()} />)}
      </div>
    </div>
  );
}

function PathwayCard({ p, onSaved }: { p: Pathway; onSaved: () => void }) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState(p.review_note);
  const [busy, setBusy] = useState(false);
  const save = async (status: Pathway["review_status"]) => {
    setBusy(true);
    await api.reviewPathway(p.id, status, "Class teacher", note);
    setBusy(false);
    onSaved();
  };
  return (
    <Card className="overflow-hidden">
      <button onClick={() => setOpen((o) => !o)} className="flex w-full items-center gap-4 p-4 text-left">
        <span className="w-20 shrink-0 font-mono text-xs font-bold text-ink-400">{p.id}</span>
        <div className="min-w-0 flex-1">
          <div className="text-xs font-extrabold text-ink-400">
            {p.theme} › {p.topic_name} › {p.concept_name}
          </div>
          <div className="truncate text-[15px] font-extrabold text-ink-900">{p.diagnostic_question}</div>
        </div>
        <span className={cn("shrink-0 rounded-full px-2.5 py-1 text-xs font-extrabold", STATUS[p.review_status].tone)}>{STATUS[p.review_status].label}</span>
        <ChevronDown className={cn("h-5 w-5 shrink-0 text-ink-400 transition", open && "rotate-180")} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <div className="grid gap-4 border-t border-ink-100 p-5 md:grid-cols-2">
              <Field label="Learning objective">{p.learning_objective}</Field>
              <Field label="Mastery criterion">{p.mastery_criterion}</Field>
              <Field label="Expected explanation">{p.expected_explanation}</Field>
              <Field label="Reasoning points (required ones in bold)">
                <ul className="list-disc space-y-0.5 pl-4">
                  {p.reasoning_points.map((r) => (
                    <li key={r} className={p.required_points.includes(r) ? "font-extrabold text-ink-900" : ""}>
                      {r}
                    </li>
                  ))}
                </ul>
              </Field>
              <Field label="Linked misconceptions">
                {p.misconceptions.length === 0 ? (
                  "—"
                ) : (
                  <ul className="space-y-1">
                    {p.misconceptions.map((m) => (
                      <li key={m.id}>
                        <b className="text-coral-700">{m.label}:</b> “{m.statement}” → {m.corrective_target}
                      </li>
                    ))}
                  </ul>
                )}
              </Field>
              <Field label="Follow-up (transfer) questions">
                <ol className="list-decimal space-y-1 pl-4">
                  {p.transfer_questions.map((t) => (
                    <li key={t.id}>
                      {t.prompt} <span className="text-ink-400">— {t.expected_answer}</span>
                    </li>
                  ))}
                </ol>
              </Field>
              <div className="md:col-span-2">
                <div className="label-caps mb-1">Review note</div>
                <Textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. accept “steam” as well as “water vapour”" />
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <Button size="sm" variant="mint" disabled={busy} onClick={() => save("approved")}>
                    <Check /> Approve
                  </Button>
                  <Button size="sm" variant="coral" disabled={busy} onClick={() => save("flagged")}>
                    <Flag /> Flag for changes
                  </Button>
                  <Button size="sm" variant="ghost" disabled={busy} onClick={() => save("draft")}>
                    Reset to draft
                  </Button>
                  {p.reviewer && (
                    <span className="ml-auto flex items-center gap-1 text-xs font-bold text-ink-400">
                      <ShieldCheck className="h-3.5 w-3.5" /> {p.review_status} by {p.reviewer}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="label-caps mb-1">{label}</div>
      <div className="text-sm font-semibold leading-relaxed text-ink-700">{children}</div>
    </div>
  );
}
