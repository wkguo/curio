"use client";

import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, CheckCircle2, Lock, MessageSquareOff, Presentation, ShieldCheck, Sparkles, Undo2 } from "lucide-react";
import Link from "next/link";

import { Logo } from "@/components/layout/logo";
import { Curio } from "@/components/mascot/curio";
import { Button } from "@/components/ui/button";
import { Emoji } from "@/components/ui/emoji";

const LOOP = [
  { k: "Verify", e: "magnifying_glass", d: "Check the answer AND the reasoning behind it.", c: "#7C5CFF" },
  { k: "Validate", e: "brain", d: "Diagnose the exact misconception, not just “wrong”.", c: "#F2703A" },
  { k: "Teach", e: "light_bulb", d: "Pick a strategy: analogy, counterexample, Socratic question…", c: "#F5A70A" },
  { k: "Question back", e: "rocket", d: "A new situation that tests the same idea.", c: "#3D7BF5" },
  { k: "Confirm", e: "trophy", d: "Mastery grows only when understanding transfers.", c: "#1FB978" },
];

const PIPELINE = ["Safety & privacy check", "Curriculum grounding", "Explanation-aware verification", "Misconception diagnosis", "Targeted teaching (or clarify)", "Transfer question back", "Evidence-based mastery gate"];

const floaters = [
  { e: "fire", x: "-7%", y: "6%", s: 54, d: 0 },
  { e: "magnet", x: "96%", y: "0%", s: 50, d: 0.6 },
  { e: "droplet", x: "100%", y: "70%", s: 44, d: 1.1 },
  { e: "thermometer", x: "-6%", y: "72%", s: 46, d: 0.3 },
  { e: "test_tube", x: "50%", y: "-4%", s: 38, d: 0.9 },
];

export default function Landing() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-cream">
      <div className="blob-bg">
        {/* Nav */}
        <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
          <Logo />
          <nav className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
              <Link href="/teacher">
                <Presentation /> Teacher view
              </Link>
            </Button>
            <Button asChild size="sm">
              <Link href="/dashboard">Start demo</Link>
            </Button>
          </nav>
        </header>

        {/* Hero */}
        <section className="relative mx-auto grid max-w-6xl items-center gap-12 px-5 pb-20 pt-8 lg:grid-cols-[1.05fr_1fr] lg:pt-14">
          {floaters.map((f) => (
            <motion.div
              key={f.e}
              className="pointer-events-none absolute hidden xl:block"
              style={{ left: f.x, top: f.y }}
              animate={{ y: [0, -12, 0], rotate: [0, 6, 0] }}
              transition={{ duration: 5, repeat: Infinity, delay: f.d, ease: "easeInOut" }}
            >
              <Emoji name={f.e} size={f.s} className="opacity-90 drop-shadow-lg" />
            </motion.div>
          ))}

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="relative">
            <span className="inline-flex items-center gap-2 rounded-full bg-white px-3.5 py-1.5 text-xs font-extrabold text-curio-700 shadow-soft ring-1 ring-curio-100">
              <Sparkles className="h-3.5 w-3.5" /> AI learning verification · Singapore P5–P6 Science
            </span>
            <h1 className="mt-5 text-balance text-5xl font-black leading-[1.02] text-ink-900 sm:text-6xl lg:text-[68px]">
              Don&apos;t just answer.
              <br />
              <span className="relative inline-block text-curio-500">
                Understand.
                <svg className="absolute -bottom-3 left-0 w-full" viewBox="0 0 300 18" fill="none" preserveAspectRatio="none">
                  <motion.path d="M4 12 C 80 2, 200 2, 296 10" stroke="#FFC53D" strokeWidth="7" strokeLinecap="round" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.6, duration: 0.8 }} />
                </svg>
              </span>
            </h1>
            <p className="mt-7 max-w-xl text-lg font-semibold leading-relaxed text-ink-600">
              Curio doesn&apos;t simply check whether students get the right answer. It verifies whether they understand <b className="text-ink-900">why</b> — finds the misconception, teaches the missing idea, then asks a brand-new question to confirm it stuck.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Button asChild size="xl">
                <Link href="/dashboard">
                  Try it as Alex <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="xl" variant="secondary">
                <Link href="/teacher">See the teacher view</Link>
              </Button>
            </div>
            <div className="mt-8 flex items-center gap-5 text-sm font-bold text-ink-500">
              <span className="flex items-center gap-1.5">
                <Emoji name="books" size={22} /> 24 concept pathways
              </span>
              <span className="flex items-center gap-1.5">
                <Emoji name="teacher" size={22} /> Teacher-grade traces
              </span>
            </div>
          </motion.div>

          <HeroDemo />
        </section>
      </div>

      {/* Chatbot vs Curio */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <div className="label-caps">Why Curio is different</div>
          <h2 className="mt-2 text-4xl font-black text-ink-900">Understanding &gt; answer accuracy</h2>
          <p className="mt-3 text-[17px] font-semibold text-ink-500">A correct final answer does not automatically mean mastery. Curio is built around that one idea.</p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-[1fr_1.4fr]">
          <div className="card-base p-7 opacity-90">
            <div className="flex items-center gap-2 text-lg font-black text-ink-500">
              <MessageSquareOff className="h-5 w-5" /> A normal chatbot
            </div>
            <div className="mt-8 flex flex-col items-center gap-2">
              {["Student question", "LLM", "Answer"].map((s, i) => (
                <div key={s} className="flex flex-col items-center gap-2">
                  <div className="rounded-2xl bg-ink-100 px-6 py-3 font-extrabold text-ink-500">{s}</div>
                  {i < 2 && <div className="h-6 w-0.5 bg-ink-200" />}
                </div>
              ))}
            </div>
            <p className="mt-8 text-center text-sm font-bold text-ink-400">Gives the answer away. Never checks if the student understood.</p>
          </div>
          <div className="card-base relative overflow-hidden p-7">
            <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-curio-100 blur-2xl" />
            <div className="relative flex items-center gap-2 text-lg font-black text-curio-600">
              <Curio size={34} /> Curio&apos;s pedagogical harness
            </div>
            <ol className="relative mt-6 grid gap-2.5 sm:grid-cols-2">
              <li className="rounded-2xl bg-ink-900 px-4 py-3 font-extrabold text-white sm:col-span-2">Student response</li>
              {PIPELINE.map((s, i) => (
                <motion.li
                  key={s}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, amount: 0.15 }}
                  transition={{ delay: i * 0.07 }}
                  className="flex items-center gap-3 rounded-2xl bg-curio-50 px-4 py-3 font-extrabold text-ink-800 ring-1 ring-curio-100"
                >
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-curio-500 text-xs font-black text-white">{i + 1}</span>
                  {s}
                </motion.li>
              ))}
              <li className="rounded-2xl bg-mint-500 px-4 py-3 font-extrabold text-white">Knowledge state updated ✓</li>
            </ol>
          </div>
        </div>
      </section>

      {/* The loop */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-6xl px-5">
          <div className="text-center">
            <div className="label-caps">The core loop</div>
            <h2 className="mt-2 text-4xl font-black text-ink-900">Verify → Validate → Teach → Question back → Confirm</h2>
          </div>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {LOOP.map((l, i) => (
              <motion.div
                key={l.k}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.15 }}
                transition={{ delay: i * 0.08 }}
                className="card-base relative p-5 text-center"
              >
                <div className="absolute inset-x-0 top-0 h-1.5 rounded-t-3xl" style={{ background: l.c }} />
                <div className="mx-auto grid h-20 w-20 place-items-center rounded-3xl" style={{ background: `${l.c}18` }}>
                  <Emoji name={l.e} size={50} />
                </div>
                <div className="mt-4 text-xs font-black" style={{ color: l.c }}>
                  STEP {i + 1}
                </div>
                <h3 className="text-lg font-black text-ink-900">{l.k}</h3>
                <p className="mt-1 text-sm font-semibold text-ink-500">{l.d}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Evidence */}
      <section className="mx-auto max-w-6xl px-5 pt-20">
        <div className="card-base grid items-center gap-8 p-8 md:grid-cols-[1.2fr_1fr]">
          <div>
            <div className="label-caps">Research question</div>
            <h2 className="mt-2 text-3xl font-black text-ink-900">Can an AI tutor verify understanding before declaring mastery?</h2>
            <p className="mt-3 text-[16px] font-semibold text-ink-500">
              Curio is not another question bank. Every pathway is grounded in the syllabus and reviewed by a teacher. Every decision is traced. And Curio is
              benchmarked against an answer-only grader on teacher-labelled cases of correct, poor-reasoning, incomplete, misconception, ambiguous and unsafe
              responses.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button asChild>
                <Link href="/teacher/evaluation">
                  See the benchmark <ArrowRight />
                </Link>
              </Button>
              <Button asChild variant="secondary">
                <Link href="/teacher/content">Review content pathways</Link>
              </Button>
            </div>
          </div>
          <ol className="space-y-2">
            {[
              ["magnifying_glass", "Explanation-aware verification"],
              ["brain", "Misconception diagnosis"],
              ["light_bulb", "Targeted teaching"],
              ["rocket", "Transfer-based questioning"],
              ["trophy", "Evidence-based mastery gating"],
            ].map(([e, t], i) => (
              <li key={t} className="flex items-center gap-3 rounded-2xl bg-cream px-4 py-2.5 font-extrabold text-ink-800">
                <span className="text-xs font-black text-curio-500">{i + 1}</span>
                <Emoji name={e} size={26} /> {t}
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Safety */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="grid items-center gap-10 md:grid-cols-2">
          <div>
            <div className="label-caps">Built for 10–12 year olds</div>
            <h2 className="mt-2 text-4xl font-black text-ink-900">Safe by design</h2>
            <p className="mt-3 text-[17px] font-semibold text-ink-500">Curio is a focused science tutor, not an open chatbot.</p>
          </div>
          <ul className="grid gap-3 sm:grid-cols-2">
            {[
              { i: ShieldCheck, t: "Curriculum-bounded", d: "Stays inside the syllabus; no general chat." },
              { i: Lock, t: "Minimal data (PDPC)", d: "Personal details are auto-hidden before saving; families can delete data." },
              { i: CheckCircle2, t: "Curated content first", d: "Teacher-authored teaching is preferred over generated text." },
              { i: Undo2, t: "Ask or defer, never guess", d: "Unclear answers get a clarifying question — or go to the teacher." },
            ].map(({ i: Icon, t, d }) => (
              <li key={t} className="card-base p-5">
                <Icon className="h-6 w-6 text-mint-500" />
                <div className="mt-2 font-black text-ink-900">{t}</div>
                <div className="text-sm font-semibold text-ink-500">{d}</div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-5 pb-24">
        <div className="relative overflow-hidden rounded-[2.5rem] bg-curio-500 px-8 py-14 text-center text-white shadow-float">
          <div className="absolute -left-10 -top-10 h-52 w-52 rounded-full bg-white/10" />
          <div className="absolute -bottom-16 -right-8 h-64 w-64 rounded-full bg-sun-400/30" />
          <Curio size={110} mood="wave" className="relative mx-auto" />
          <h2 className="relative mt-4 text-4xl font-black">From correct answers to real understanding.</h2>
          <p className="relative mt-2 text-lg font-bold text-curio-100">Take the 2-minute demo as Alex, a Primary 5 student.</p>
          <Button asChild size="xl" variant="sun" className="relative mt-8">
            <Link href="/learn?topic=heat_transfer">
              Start learning <ArrowRight />
            </Link>
          </Button>
        </div>
        <p className="mt-8 text-center text-xs font-bold text-ink-400">Curio MVP · 3D emoji art: Microsoft Fluent Emoji (MIT)</p>
      </section>
    </div>
  );
}

function HeroDemo() {
  return (
    <motion.div initial={{ opacity: 0, y: 24, rotate: 1.5 }} animate={{ opacity: 1, y: 0, rotate: 0 }} transition={{ delay: 0.2, duration: 0.7 }} className="relative">
      <div className="card-base relative space-y-3 p-5 shadow-float">
        <div className="flex items-center gap-3 rounded-2xl bg-cream p-3">
          <Emoji name="spoon" size={44} />
          <p className="text-[15px] font-extrabold text-ink-900">Why does a metal spoon feel colder than a wooden spoon in the same room?</p>
        </div>
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.8 }} className="ml-auto w-fit max-w-[80%] rounded-3xl rounded-br-lg bg-curio-500 px-4 py-2.5 text-sm font-bold text-white">
          Because metal is colder than wood.
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.4 }} className="rounded-3xl border-2 border-curio-100 bg-white p-4">
          <div className="label-caps">Curio is checking your reasoning…</div>
          <div className="mt-2 space-y-2 text-sm font-bold text-ink-700">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.8 }} className="flex items-start gap-2">
              <CheckCircle2 className="h-5 w-5 shrink-0 text-mint-500" /> You noticed that metal and wood behave differently.
            </motion.div>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.3 }} className="flex items-start gap-2 rounded-2xl bg-sun-50 p-2.5">
              <AlertTriangle className="h-5 w-5 shrink-0 text-sun-600" />
              <span>
                But one idea needs another look: <i>“Metal is naturally colder.”</i> Both spoons may be at the same temperature!
              </span>
            </motion.div>
          </div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 2.9 }} className="flex items-center justify-between rounded-2xl bg-mint-50 px-4 py-3">
          <span className="flex items-center gap-2 text-sm font-extrabold text-mint-700">
            <Emoji name="check_mark_button" size={22} /> Heat Conduction mastery confirmed
          </span>
          <span className="font-black tabular-nums text-mint-600">52% → 76%</span>
        </motion.div>
      </div>
      <motion.div className="absolute -bottom-12 -left-10 hidden sm:block" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.5, type: "spring" }}>
        <Curio size={120} mood="happy" />
      </motion.div>
    </motion.div>
  );
}
