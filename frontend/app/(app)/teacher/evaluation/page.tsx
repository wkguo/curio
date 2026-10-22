"use client";

import { FlaskConical, Play } from "lucide-react";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { SectionTitle } from "@/components/shared/section-title";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Emoji } from "@/components/ui/emoji";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip } from "@/components/ui/tooltip";
import { api, CurioError, FRIENDLY_ERROR } from "@/lib/api";
import { useEvaluation, useLLMComparison, useOffline } from "@/lib/hooks";
import { CLASSIFICATION, SAFETY_LABEL } from "@/lib/labels";
import { cn, timeAgo } from "@/lib/utils";
import type { Classification, ComparisonMetrics, EvalReport } from "@/types/api";

const f = (x: number | null | undefined) => (x == null ? "—" : `${(x * 100).toFixed(1)}%`);
const CURIO = "#7C5CFF";
const BASE = "#F2703A";
const CLASSES: Classification[] = ["correct", "incomplete", "misconception", "incorrect", "unclear", "guess", "blocked"];

export default function EvaluationPage() {
  const { data, error, mutate } = useEvaluation();
  const offline = useOffline();
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="Teacher view · evaluation"
        title="Benchmark & validation"
        subtitle="A benchmark with draft labels awaiting teacher review. Compare answer and reasoning checks with an answer-only marker."
        actions={
          <Button
            variant="secondary"
            disabled={running || offline}
            onClick={async () => {
              setRunning(true);
              setRunError(null);
              try {
                await mutate(await api.runEvaluation(), { revalidate: false });
              } catch (e) {
                setRunError(e instanceof CurioError ? e.message : FRIENDLY_ERROR);
              } finally {
                setRunning(false);
              }
            }}
          >
            <Play className={cn(running && "animate-pulse")} /> {running ? "Running…" : "Re-run benchmark"}
          </Button>
        }
      />
      {offline && <p role="status" className="mt-4 rounded-2xl bg-sun-50 p-3 text-sm font-bold text-sun-700">Recorded report. Connect to the live app to run a new evaluation.</p>}
      {runError && <p role="alert" className="mt-4 text-sm font-bold text-coral-600">{runError}</p>}
      <ModelComparison />
      {!data && error ? (
        <div role="alert" className="card-base mt-6 p-6">
          <p className="mb-4 font-bold text-ink-700">The report could not load. Please try again.</p>
          <Button variant="secondary" onClick={() => void mutate()}>Try again</Button>
        </div>
      ) : !data ? <Skeleton className="mt-6 h-96" /> : <Report r={data} />}
    </div>
  );
}

function ModelComparison() {
  const { data, error } = useLLMComparison();
  const [split, setSplit] = useState<"test" | "all">("test");
  if (!data?.available) return (
    <Card className="mt-5 p-6">
      <SectionTitle emoji={<FlaskConical className="h-5 w-5 text-curio-500" />}>Same-model comparison</SectionTitle>
      <p className="text-sm font-semibold text-ink-600">{error ? "The model-comparison report could not load." : "No completed same-model comparison is available yet. The answer-only marker below is a rules baseline, not an LLM."}</p>
    </Card>
  );
  const metrics: [keyof ComparisonMetrics, string][] = [
    ["classification_accuracy", "Classification accuracy"],
    ["false_mastery_rate", "False mastery · lower is better"],
    ["correct_credit_rate", "Fully correct answers credited"],
    ["safety_catch_rate", "Safety & privacy catch rate"],
    ["decision_consistency", "Same decision on repeat"],
    ["raw_personal_data_sent_to_provider", "Matched personal data sent to model"],
  ];
  const systems = Object.values(data.systems);
  return (
    <Card className="mt-5 p-6">
      <SectionTitle emoji={<FlaskConical className="h-5 w-5 text-curio-500" />}>Same-model comparison</SectionTitle>
      <p className="mb-3 text-sm font-semibold text-ink-600">{data.model} · {data.cases} cases · same curriculum key. Draft labels await teacher review. Results apply to this model and setup.</p>
      <div className="mb-4 flex gap-2">
        {(["test", "all"] as const).map((s) => (
          <Button key={s} variant={split === s ? "default" : "secondary"} size="sm" onClick={() => setSplit(s)}>
            {s === "test" ? "Held-out" : "All cases"}
          </Button>
        ))}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[600px] text-left text-sm">
          <thead><tr className="text-ink-500"><th className="py-3">Metric</th>{systems.map(s => <th key={s.label} className="px-3">{s.label}<span className="block text-xs">n={s.metrics[split].n}</span></th>)}</tr></thead>
          <tbody>{metrics.map(([key, label]) => <tr key={key} className="border-t border-ink-100 font-bold text-ink-700"><td className="py-3">{label}</td>{systems.map(s => <td className="px-3 tabular-nums" key={s.label}>{f(s.metrics[split][key])}</td>)}</tr>)}</tbody>
        </table>
      </div>
      <p className="mt-4 text-xs font-semibold leading-relaxed text-ink-500">False mastery here measures one answer against a draft label, not learning gains or mastery after teaching. Read it alongside correct-answer credit. Data masking uses the same patterns as redaction; it is a design check, not a test of every kind of personal data. One historical safety example informed the rules.</p>
    </Card>
  );
}

function Report({ r }: { r: EvalReport }) {
  const g = r.understanding_gate;
  const [filter, setFilter] = useState<"errors" | "all" | "test">("errors");
  const rows = useMemo(
    () => r.cases.filter((c) => (filter === "all" ? true : filter === "test" ? c.split === "test" : c.split === "dev" && !c.match)),
    [r.cases, filter],
  );

  return (
    <>
      <p className="mt-3 text-xs font-bold text-ink-400">
        {r.benchmark.cases} cases · {r.mode} mode · run {timeAgo(r.generated_at)} · labels: {r.benchmark.labeller}
      </p>

      {/* Research question */}
      <Card className="mt-5 overflow-hidden">
        <div className="grid gap-6 p-6 lg:grid-cols-[1fr_1.1fr]">
          <div className="min-w-0">
            <SectionTitle emoji={<Emoji name="direct_hit" size={24} />}>Does verification stop false mastery?</SectionTitle>
            <p className="text-sm font-semibold leading-relaxed text-ink-600">
              An answer-only marker credits the final answer. Curio checks the reasoning too. Among responses with draft labels of{" "}
              <b>not showing understanding</b> (n={g.not_understood_cases}), how often would each grader wrongly credit mastery?
            </p>
            <div className="mt-5 space-y-4">
              <GateBar label={`All not-understood responses (n=${g.not_understood_cases})`} curio={g.curio_false_mastery_rate} base={g.baseline_false_mastery_rate} />
              <GateBar label={`Right answer, poor reasoning (n=${g.poor_reasoning_cases})`} curio={g.curio_false_mastery_on_poor_reasoning} base={g.baseline_false_mastery_on_poor_reasoning} />
              <GateBar label={`Fully correct responses credited (n=${g.understood_cases}) — higher is better`} curio={g.curio_correct_credit_rate} base={g.baseline_correct_credit_rate} />
            </div>
            <div className="mt-3 flex gap-4 text-xs font-bold text-ink-500">
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-sm" style={{ background: CURIO }} /> Curio
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-sm" style={{ background: BASE }} /> Answer-only baseline
              </span>
            </div>
          </div>
          <div className="min-w-0">
            <SectionTitle emoji={<FlaskConical className="h-5 w-5 text-curio-500" />}>Development vs held-out</SectionTitle>
            <p className="mb-3 text-sm font-semibold text-ink-600">
              Use <b>dev</b> examples to improve the rules; reserve <b>test</b> cases (every 3rd id) for evaluation. Labels await teacher review. One earlier safety change used a test example, so safety results are optimistic.
            </p>
            <div className="overflow-x-auto"><table className="min-w-[450px] w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] font-extrabold uppercase tracking-wider text-ink-400">
                  <th className="py-1.5">Split</th>
                  <th>Cases</th>
                  <th>Class. acc.</th>
                  <th>Safety catch</th>
                  <th>False mastery (Curio / base)</th>
                </tr>
              </thead>
              <tbody className="font-bold text-ink-800">
                {(["dev", "test"] as const).map((k) => {
                  const s = r.by_split[k];
                  return (
                    <tr key={k} className="border-t border-ink-100">
                      <td className="py-2 capitalize">{k === "test" ? "Test (held-out)" : "Dev"}</td>
                      <td>{s.cases}</td>
                      <td>{f(s.classification_accuracy)}</td>
                      <td>{f(s.safety_catch_rate)}</td>
                      <td>
                        {f(s.curio_false_mastery_rate)} / {f(s.baseline_false_mastery_rate)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table></div>
          </div>
        </div>
      </Card>

      {/* Headline metrics */}
      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
        {Object.entries(r.metrics).map(([k, v]) => (
          <Card key={k} className="p-4">
            <div className="text-2xl font-black text-ink-900">{f(v)}</div>
            <div className="text-xs font-extrabold capitalize text-ink-500">{k.replace(/_/g, " ")}</div>
          </Card>
        ))}
      </div>

      <div className="mt-5 grid min-w-0 grid-cols-1 gap-5 lg:grid-cols-2">
        <Card className="min-w-0 p-6">
          <SectionTitle emoji={<Emoji name="puzzle_piece" size={24} />}>Confusion matrix (gold → predicted)</SectionTitle>
          <Confusion r={r} />
        </Card>
        <Card className="min-w-0 p-6">
          <SectionTitle emoji={<Emoji name="warning" size={24} />}>Safety & privacy layer</SectionTitle>
          <ul className="space-y-3">
            {Object.entries(r.safety).map(([k, v]) => (
              <li key={k}>
                <div className="mb-1 flex justify-between text-sm font-extrabold text-ink-700">
                  <span>{SAFETY_LABEL[k] ?? k}</span>
                  <span className="tabular-nums text-ink-500">
                    {v.caught}/{v.cases} caught
                  </span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-ink-100">
                  <div className="h-full rounded-full bg-curio-500" style={{ width: `${v.cases ? (v.caught / v.cases) * 100 : 0}%` }} />
                </div>
              </li>
            ))}
          </ul>
          <p className="mt-4 rounded-2xl bg-sun-50 p-3 text-xs font-bold text-sun-700">
            Pattern rules generalise poorly to unseen wording. Before a pilot, add an LLM-based safety classifier as a second layer and re-run this benchmark
            (proposal phase 4 decision gate).
          </p>
        </Card>
      </div>

      <Card className="mt-5 p-6">
        <SectionTitle
          emoji={<Emoji name="magnifying_glass" size={24} />}
          action={
            <div className="flex gap-1 rounded-xl bg-ink-100 p-1 text-xs font-extrabold">
              {(["errors", "test", "all"] as const).map((k) => (
                <button key={k} onClick={() => setFilter(k)} className={cn("rounded-lg px-3 py-1.5", filter === k ? "bg-white text-ink-900 shadow-soft" : "text-ink-500")}>
                  {k === "errors" ? "Dev errors" : k === "test" ? "Held-out" : "All"}
                </button>
              ))}
            </div>
          }
        >
          Case explorer
        </SectionTitle>
        <div className="scroll-thin max-h-[520px] overflow-auto">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-white">
              <tr className="text-[11px] font-extrabold uppercase tracking-wider text-ink-400">
                <th className="py-2">Id</th>
                <th>Category</th>
                <th className="w-[40%]">Student answer</th>
                <th>Gold</th>
                <th>Curio</th>
                <th>Baseline</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id} className="border-t border-ink-100 align-top">
                  <td className="py-2 font-mono text-xs text-ink-400">
                    {c.id}
                    {c.split === "test" && <span className="ml-1 rounded bg-sky-100 px-1 text-[9px] font-extrabold text-sky-700">TEST</span>}
                  </td>
                  <td className="text-xs font-bold text-ink-500">{c.category.replace(/_/g, " ")}</td>
                  <td className="pr-3 text-[13px] font-semibold text-ink-700">“{c.answer}”</td>
                  <td>
                    <Pill c={c.gold.classification} extra={c.gold.misconception_id} />
                  </td>
                  <td>
                    <Pill c={c.pred.classification} extra={c.pred.misconception_id} wrong={!c.match} />
                  </td>
                  <td className="text-xs font-extrabold">{c.gold.classification === "blocked" ? "—" : c.pred.baseline_credit ? <span className="text-coral-600">credits</span> : <span className="text-ink-400">no credit</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}

function GateBar({ label, curio, base }: { label: string; curio: number | null | undefined; base: number | null | undefined }) {
  return (
    <div>
      <div className="mb-1.5 text-xs font-extrabold text-ink-600">{label}</div>
      {[
        ["Curio", curio, CURIO],
        ["Baseline", base, BASE],
      ].map(([name, v, color]) => (
        <div key={name as string} className="mb-1 flex items-center gap-2">
          <span className="w-16 text-[11px] font-bold text-ink-400">{name as string}</span>
          <div className="h-4 flex-1 overflow-hidden rounded-md bg-ink-100">
            <div className="h-full rounded-md transition-all duration-700" style={{ width: `${((v as number) ?? 0) * 100}%`, background: color as string }} />
          </div>
          <span className="w-14 text-right text-xs font-black tabular-nums text-ink-800">{f(v as number)}</span>
        </div>
      ))}
    </div>
  );
}

function Pill({ c, extra, wrong }: { c: Classification; extra?: string | null; wrong?: boolean }) {
  return (
    <div>
      <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-extrabold", CLASSIFICATION[c].tone, wrong && "ring-2 ring-coral-300")}>{CLASSIFICATION[c].label}</span>
      {extra && <div className="mt-0.5 text-[10px] font-bold text-ink-400">{extra}</div>}
    </div>
  );
}

function Confusion({ r }: { r: EvalReport }) {
  const max = Math.max(1, ...CLASSES.flatMap((g) => CLASSES.map((p) => r.confusion[g]?.[p] ?? 0)));
  return (
    <div className="scroll-thin overflow-x-auto">
      <table className="border-separate border-spacing-[3px] text-xs">
        <thead>
          <tr>
            <th />
            {CLASSES.map((p) => (
              <th key={p} className="w-10 pb-1 text-[9px] font-extrabold text-ink-500">
                {CLASSIFICATION[p].label.split(" ")[0]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {CLASSES.map((g) => (
            <tr key={g}>
              <td className="pr-2 text-right text-[11px] font-extrabold text-ink-600">{CLASSIFICATION[g].label.split(" ")[0]}</td>
              {CLASSES.map((p) => {
                const v = r.confusion[g]?.[p] ?? 0;
                const diag = g === p;
                return (
                  <td key={p}>
                    <Tooltip content={`gold ${g} → predicted ${p}: ${v}`}>
                      <div
                        className={cn("grid h-9 w-10 cursor-help place-items-center rounded-lg font-black tabular-nums", v ? "text-white" : "text-ink-300")}
                        style={{ background: v ? (diag ? `rgba(31,185,120,${0.25 + (0.75 * v) / max})` : `rgba(242,112,58,${0.2 + (0.8 * v) / max})`) : "#F3F2F8" }}
                      >
                        {v || "·"}
                      </div>
                    </Tooltip>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-[11px] font-bold text-ink-400">Green = agreement with the draft label; orange = disagreement. Rows: draft label; columns: Curio.</p>
    </div>
  );
}
