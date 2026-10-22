/**
 * Curio API client.
 *
 * Every call goes to the FastAPI backend through the Next.js /api rewrite. If the
 * backend is unreachable (network error / proxy 5xx), the client transparently
 * switches to OFFLINE DEMO MODE and serves fixtures exported from the real backend
 * (public/mock/fixtures.json, produced by backend/scripts/export_fixtures.py).
 *
 * A 503 with code "curio_unavailable" is the backend's deliberate, student-safe
 * error (spec §25) and is surfaced as a friendly message, never as a stack trace.
 */
import type {
  ClassAnalytics,
  Dashboard,
  EvalReport,
  Health,
  LLMComparisonReport,
  Pathway,
  PrivacySummary,
  ReplyResponse,
  ReviewItem,
  Session,
  StudentMastery,
  StudentProfile,
  SubmitResponse,
  TopicDetail,
  TopicSummary,
  TraceDetail,
  TraceSummary,
  TransferResponse,
} from "@/types/api";

export const FRIENDLY_ERROR = "Curio is having trouble checking that answer right now. Let's try this question another way.";

export class CurioError extends Error {
  constructor(message = FRIENDLY_ERROR) {
    super(message);
  }
}

// ------------------------------------------------------------------ offline store
type Listener = () => void;
const listeners = new Set<Listener>();
let offline = process.env.NEXT_PUBLIC_CURIO_OFFLINE === "1";
export const offlineStore = {
  get: () => offline,
  subscribe: (l: Listener) => {
    listeners.add(l);
    return () => listeners.delete(l);
  },
  set(v: boolean) {
    if (v !== offline) {
      offline = v;
      listeners.forEach((l) => l());
    }
  },
};
const forcedOffline = process.env.NEXT_PUBLIC_CURIO_OFFLINE === "1";

interface Fixtures {
  health: Health;
  students: StudentProfile[];
  topics: TopicSummary[];
  topic_details: Record<string, TopicDetail>;
  mastery: StudentMastery;
  dashboard: Dashboard;
  sessions: Record<string, Session>;
  analytics: ClassAnalytics;
  traces: TraceSummary[];
  trace_details: Record<string, TraceDetail>;
  flows: Record<string, { submit: SubmitResponse; reply: ReplyResponse; transfer: TransferResponse }>;
  queue: ReviewItem[];
  pathways: Pathway[];
  privacy: PrivacySummary;
  evaluation: EvalReport;
  llm_comparison?: LLMComparisonReport;
}

let fixturesPromise: Promise<Fixtures> | null = null;
function fixtures(): Promise<Fixtures> {
  fixturesPromise ??= fetch("/mock/fixtures.json")
    .then((r) => {
      if (!r.ok) throw new CurioError("The recorded demo could not load. Please try again.");
      return r.json();
    })
    .catch(() => {
      fixturesPromise = null;
      throw new CurioError("The recorded demo could not load. Please try again.");
    });
  return fixturesPromise;
}

// Offline mode keeps a small overlay so mastery visibly updates during a demo.
const overlay: Record<string, number> = {};
function applyOverlay<T extends { mastery: number; id: string }>(c: T): T {
  return c.id in overlay ? { ...c, mastery: overlay[c.id], status: overlay[c.id] >= 0.75 ? "mastered" : (c as any).status } : c;
}

async function request<T>(path: string, init: RequestInit | undefined, mock: (fx: Fixtures) => T, allowReplay = true): Promise<T> {
  if (!forcedOffline) {
    let res: Response | null = null;
    try {
      res = await fetch(path, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) }, cache: "no-store" });
    } catch {
      res = null; // network error → offline
    }
    if (res) {
      if (res.ok) {
        offlineStore.set(false);
        return (await res.json()) as T;
      }
      if (res.status === 503) {
        const body = await res.json().catch(() => null);
        if (body?.code === "curio_unavailable") throw new CurioError(body.message);
      }
      if (res.status < 500) {
        const body = await res.json().catch(() => null);
        throw new CurioError(typeof body?.detail === "string" ? body.detail : FRIENDLY_ERROR);
      }
    }
  }
  offlineStore.set(true);
  if (!allowReplay) throw new CurioError("This action needs a live connection. Please reconnect and check its status.");
  const fx = await fixtures();
  return mock(fx);
}

const post = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });
const findFlow = (fx: Fixtures, interactionId: string) =>
  Object.values(fx.flows).find((f) => f.submit.interaction_id === interactionId) ?? Object.values(fx.flows)[0];

export const api = {
  health: () => request<Health>("/api/health", undefined, (fx) => fx.health),
  students: () => request<StudentProfile[]>("/api/students", undefined, (fx) => fx.students),
  topics: (studentId?: string) =>
    request<TopicSummary[]>(`/api/curriculum/topics${studentId ? `?student_id=${studentId}` : ""}`, undefined, (fx) => fx.topics),
  topic: (topicId: string, studentId?: string) =>
    request<TopicDetail>(`/api/curriculum/topics/${topicId}${studentId ? `?student_id=${studentId}` : ""}`, undefined, (fx) => {
      const t = fx.topic_details[topicId];
      return { ...t, concepts: t.concepts.map(applyOverlay) };
    }),
  mastery: (studentId: string) =>
    request<StudentMastery>(`/api/students/${studentId}/mastery`, undefined, (fx) => ({
      ...fx.mastery,
      concepts: fx.mastery.concepts.map(applyOverlay),
      concept_mastery: { ...fx.mastery.concept_mastery, ...overlay },
    })),
  dashboard: (studentId: string) =>
    request<Dashboard>(`/api/students/${studentId}/dashboard`, undefined, (fx) => ({
      ...fx.dashboard,
      current_concepts: fx.dashboard.current_concepts.map(applyOverlay),
    })),
  startSession: (studentId: string, topicId: string, size = 5) =>
    request<Session>("/api/learning/sessions", post({ student_id: studentId, topic_id: topicId, size }), (fx) => {
      const s = fx.sessions[topicId];
      return { ...s, questions: s.questions.slice(0, size), total: Math.min(size, s.questions.length) };
    }),
  queue: (status = "open") => request<ReviewItem[]>(`/api/teacher/queue?status=${status}`, undefined, (fx) => fx.queue),
  resolveQueue: (id: string, note = "") =>
    request<{ ok: boolean }>(`/api/teacher/queue/${id}/resolve`, post({ note }), () => ({ ok: true }), false),
  pathways: (topicId?: string) =>
    request<Pathway[]>(`/api/teacher/pathways${topicId ? `?topic_id=${topicId}` : ""}`, undefined, (fx) =>
      topicId ? fx.pathways.filter((p) => p.topic_id === topicId) : fx.pathways,
    ),
  reviewPathway: (id: string, status: Pathway["review_status"], reviewer: string, note: string) =>
    request<Pathway>(`/api/teacher/pathways/${id}/review`, post({ status, reviewer, note }), (fx) => ({
      ...fx.pathways.find((p) => p.id === id)!,
      review_status: status,
      reviewer,
      review_note: note,
    }), false),
  privacy: (studentId: string) => request<PrivacySummary>(`/api/privacy/students/${studentId}`, undefined, (fx) => fx.privacy),
  deleteData: (studentId: string) =>
    request<{ ok: boolean }>(`/api/privacy/students/${studentId}`, { method: "DELETE" }, () => ({ ok: true }), false),
  evaluation: () => request<EvalReport>("/api/evaluation/report", undefined, (fx) => fx.evaluation),
  llmComparison: () => request<LLMComparisonReport>("/api/evaluation/llm-baseline", undefined, (fx) => fx.llm_comparison ?? { available: false, cases: 0, systems: {} }),
  runEvaluation: () => request<EvalReport>("/api/evaluation/run?mode=rules", { method: "POST" }, (fx) => fx.evaluation, false),
  submit: (studentId: string, questionId: string, answer: string, sessionId?: string) =>
    request<SubmitResponse>(
      "/api/learning/submit",
      post({ student_id: studentId, question_id: questionId, answer, session_id: sessionId }),
      (fx) => {
        const r = fx.flows[questionId].submit;
        if (r.mastery_change && r.mastery_after != null) overlay[r.mastery_change.concept_id] = r.mastery_after;
        return r;
      },
    ),
  reply: (studentId: string, interactionId: string, message: string) =>
    request<ReplyResponse>("/api/learning/reply", post({ student_id: studentId, interaction_id: interactionId, message }), (fx) => findFlow(fx, interactionId).reply),
  transfer: (studentId: string, interactionId: string, answer: string) =>
    request<TransferResponse>("/api/learning/transfer", post({ student_id: studentId, interaction_id: interactionId, answer }), (fx) => {
      const r = findFlow(fx, interactionId).transfer;
      if (r.mastery_change && r.mastery_after != null) overlay[r.mastery_change.concept_id] = r.mastery_after;
      return r;
    }),
  analytics: () => request<ClassAnalytics>("/api/analytics/class", undefined, (fx) => fx.analytics),
  traces: (limit = 30, studentId?: string) =>
    request<TraceSummary[]>(`/api/analytics/traces?limit=${limit}${studentId ? `&student_id=${studentId}` : ""}`, undefined, (fx) =>
      studentId ? fx.traces.filter((t) => t.student_id === studentId) : fx.traces.slice(0, limit),
    ),
  trace: (id: string) =>
    request<TraceDetail>(`/api/analytics/traces/${id}`, undefined, (fx) => fx.trace_details[id] ?? Object.values(fx.trace_details)[0]),
  resetDemo: () =>
    request<{ ok: boolean }>("/api/demo/reset", { method: "POST" }, () => {
      Object.keys(overlay).forEach((k) => delete overlay[k]);
      return { ok: true };
    }),
};
