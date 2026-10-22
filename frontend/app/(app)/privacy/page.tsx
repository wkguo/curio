"use client";

import { Check, Lock, Trash2, X } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { CurioSays } from "@/components/mascot/curio";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Emoji } from "@/components/ui/emoji";
import { api, CurioError, FRIENDLY_ERROR } from "@/lib/api";
import { useOffline, usePrivacy } from "@/lib/hooks";
import { useStudent } from "@/lib/student-context";

const LABEL: Record<string, string> = {
  answers_and_dialogue: "Answers & chat turns",
  mastery_records: "Concept mastery records",
  mastery_history_events: "Mastery history points",
  decision_traces: "Curio decision traces",
  learning_sessions: "Learning sessions",
};

export default function PrivacyPage() {
  const { data, mutate } = usePrivacy();
  const offline = useOffline();
  const { studentId, refreshAll, resetDemo } = useStudent();
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runAction = async (action: () => Promise<unknown>, success: string) => {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await action();
      setConfirm(false);
      await mutate();
      refreshAll();
      setMessage(success);
    } catch (e) {
      setError(e instanceof CurioError ? e.message : FRIENDLY_ERROR);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-8 sm:py-8">
      <PageHeader
        eyebrow="Privacy & safety"
        title="Your data, kept small and safe"
        subtitle="See what Curio stores, how common personal details are masked, and how to remove learning records."
      />
      <div className="mt-6">
        <CurioSays mood="happy">
          Please keep your name, phone number, address and IC out of your answers. I can hide common contact details, but I might miss something. 🔒
        </CurioSays>
      </div>
      {offline && <p role="status" className="mt-4 rounded-2xl bg-sun-50 p-3 text-sm font-bold text-sun-700">These are recorded demo records. Connect to the live app to view or delete current learning data.</p>}
      {error && <p role="alert" className="mt-4 text-sm font-bold text-coral-600">{error}</p>}
      {message && <p role="status" className="mt-4 text-sm font-bold text-mint-700">{message}</p>}

      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <Card className="p-6">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-black text-ink-900">
            <Emoji name="clipboard" size={24} /> What Curio keeps
          </h2>
          <ul className="space-y-2">
            {data?.data_categories.map((d) => (
              <li key={d} className="flex gap-2 text-sm font-semibold text-ink-700">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-mint-500" strokeWidth={3} /> {d}
              </li>
            ))}
          </ul>
        </Card>
        <Card className="p-6">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-black text-ink-900">
            <Lock className="h-5 w-5 text-curio-500" /> What Curio never asks for
          </h2>
          <ul className="space-y-2">
            {data?.not_collected.map((d) => (
              <li key={d} className="flex gap-2 text-sm font-semibold text-ink-700">
                <X className="mt-0.5 h-4 w-4 shrink-0 text-coral-500" strokeWidth={3} /> {d}
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card className="mt-5 p-6">
        <h2 className="mb-1 text-lg font-black text-ink-900">Stored for this student right now</h2>
        <p className="mb-4 text-sm font-semibold text-ink-500">Records older than {data?.retention_days ?? 365} days are removed each time the server starts.</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {data &&
            Object.entries(data.stored).map(([k, v]) => (
              <div key={k} className="rounded-2xl bg-ink-50 p-3 text-center">
                <div className="text-2xl font-black text-ink-900">{v}</div>
                <div className="text-[11px] font-extrabold text-ink-500">{LABEL[k] ?? k}</div>
              </div>
            ))}
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-3">
          {!confirm ? (
            <Button variant="secondary" disabled={busy || offline || !data} onClick={() => setConfirm(true)}>
              <Trash2 /> Delete my learning data
            </Button>
          ) : (
            <>
              <span className="text-sm font-bold text-coral-600">This removes all answers, traces and mastery for this student. Sure?</span>
              <Button
                variant="coral"
                disabled={busy || offline}
                onClick={() => void runAction(() => api.deleteData(studentId), "Your learning records were deleted.")}
              >
                {busy ? "Deleting…" : "Yes, delete"}
              </Button>
              <Button variant="ghost" disabled={busy} onClick={() => setConfirm(false)}>
                Cancel
              </Button>
            </>
          )}
          <Button variant="ghost" disabled={busy} onClick={() => void runAction(resetDemo, offline ? "Recorded demo restarted." : "Demo data restored.")}>
            {offline ? "Restart recorded demo" : "Restore demo data"}
          </Button>
        </div>
      </Card>

      <Card className="mt-5 p-6">
        <h2 className="mb-3 text-lg font-black text-ink-900">How Curio keeps conversations safe</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            ["shield", "Common phone, email and IC formats are hidden before saving or sending to a model. Names and unfamiliar address formats may be missed."],
            ["teacher", "If a message sounds like someone is upset or unsafe, Curio stops, shares helplines and alerts the teacher."],
            ["books", "Curio only talks about the science question — off-topic chat and tricks to change its rules are redirected."],
            ["magnifying_glass", "When Curio can't tell what you mean, it asks you — or asks your teacher — instead of guessing."],
          ].map(([e, t]) => (
            <div key={t} className="flex gap-3 rounded-2xl bg-ink-50 p-3 text-sm font-semibold text-ink-700">
              <Emoji name={e === "shield" ? "check_mark_button" : e} size={26} className="shrink-0" /> {t}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
