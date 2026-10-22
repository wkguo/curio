// Mirrors backend/schemas/api.py and backend/schemas/harness.py. Keep in sync.

export type MasteryStatus = "mastered" | "learning" | "needs_practice" | "new" | "locked";
export type MisconceptionType =
  | "FACTUAL_ERROR"
  | "CAUSAL_ERROR"
  | "CONCEPT_CONFUSION"
  | "MISSING_STEP"
  | "OVERGENERALIZATION"
  | "VOCABULARY_CONFUSION"
  | "CORRECT_BUT_INCOMPLETE"
  | "GUESS_WITHOUT_REASONING";
export type TeachingStrategy =
  | "DIRECT_HINT"
  | "SOCRATIC_QUESTION"
  | "ANALOGY"
  | "COUNTEREXAMPLE"
  | "SIMPLER_EXPLANATION"
  | "PREREQUISITE_REVIEW"
  | "VISUAL_EXPLANATION"
  | "TRANSFER_EXAMPLE"
  | "CLARIFY";
export type Classification = "correct" | "incomplete" | "misconception" | "incorrect" | "unclear" | "guess" | "blocked";
export type LearningPhase =
  | "attempt"
  | "blocked"
  | "clarifying"
  | "teaching"
  | "transfer"
  | "reteach"
  | "mastered"
  | "verified"
  | "revisit"
  | "deferred";
export type StepMode = "llm" | "rules" | "fallback";

export interface Health {
  status: string;
  harness_mode: string;
  llm: string;
  llm_available: boolean;
  model: string | null;
  offline?: boolean;
}

export interface TopicSummary {
  topic_id: string;
  name: string;
  subject: string;
  level: string;
  emoji: string;
  color: string;
  tagline: string;
  description: string;
  concept_count: number;
  question_count: number;
  mastery: number | null;
  theme?: string;
  syllabus_ref?: string;
}

export interface ConceptNode {
  id: string;
  topic_id: string;
  name: string;
  emoji: string;
  summary: string;
  learning_objective: string;
  key_ideas: string[];
  prerequisites: string[];
  position: { x: number; y: number };
  mastery: number;
  status: MasteryStatus;
  attempts: number;
  verified: number;
  misconceptions: string[];
  mastery_criterion?: string;
}

export interface MisconceptionCard {
  id: string;
  label: string;
  statement: string;
  corrective_target: string;
  concept: string;
  type: MisconceptionType;
}

export interface TopicDetail extends TopicSummary {
  concepts: ConceptNode[];
  edges: { source: string; target: string }[];
  misconceptions: MisconceptionCard[];
}

export interface StudentProfile {
  id: string;
  display_name: string;
  level: string;
  class_name: string;
  avatar: string;
  streak_days: number;
  xp: number;
  is_demo: boolean;
}

export interface TopicProgress {
  topic_id: string;
  name: string;
  emoji: string;
  color: string;
  mastery: number;
  mastered: number;
  learning: number;
  total: number;
}

export interface StudentMastery {
  student_id: string;
  concept_mastery: Record<string, number>;
  concepts: ConceptNode[];
  topics: TopicProgress[];
}

export interface ActivityItem {
  id: string;
  kind: "initial" | "transfer";
  topic_id: string;
  concept_id: string;
  concept_name: string;
  question_prompt: string;
  result: "verified" | "learning" | "needs_practice";
  mastery_before: number | null;
  mastery_after: number | null;
  created_at: string;
}

export interface Badge {
  id: string;
  name: string;
  emoji: string;
  description: string;
  earned: boolean;
}

export interface Dashboard {
  student: StudentProfile;
  topics: TopicProgress[];
  current_topic: TopicProgress;
  current_concepts: ConceptNode[];
  today: { questions_answered: number; verified: number; xp_today: number; goal: number };
  recent_activity: ActivityItem[];
  next_up: { topic_id: string; concept_id: string; concept_name: string; reason: string } | null;
  insight: string;
  history: { date: string; mastery: number; answers: number }[];
  badges: Badge[];
}

export interface QuestionCard {
  id: string;
  topic_id: string;
  concept_id: string;
  concept_name: string;
  prompt: string;
  emoji: string;
  difficulty: number;
  hints: string[];
  demo_answers: { misconception?: string; dialogue?: string; correct?: string };
}

export interface Session {
  session_id: string;
  topic_id: string;
  topic_name: string;
  topic_color: string;
  questions: QuestionCard[];
  current_index: number;
  total: number;
}

export interface DetectedMisconception {
  id: string | null;
  type: MisconceptionType;
  statement: string;
  student_claim: string;
  concept: string;
  severity: "low" | "medium" | "high";
  corrective_target: string;
  label: string;
}

export interface Verification {
  answer_correct: boolean;
  reasoning_correct: boolean;
  confidence: number;
  quality: "correct" | "partially_correct" | "incorrect";
  concepts_detected: string[];
  missing_concepts: string[];
  reasoning_points_hit: string[];
  reasoning_points_missed: string[];
  misconceptions: DetectedMisconception[];
  is_guess: boolean;
  classification: Classification;
  reasoning_summary: string;
}

export interface Diagnosis {
  type: MisconceptionType | null;
  misconception_id: string | null;
  label: string;
  concept: string;
  student_claim: string;
  corrective_target: string;
  is_repeated: boolean;
  previous_occurrences: number;
  classification: Classification;
  summary: string;
}

export interface AnalysisFeedback {
  headline: string;
  strengths: string[];
  concerns: { claim: string; note: string }[];
  nudge: string;
  tone: "celebrate" | "encourage" | "investigate";
}

export interface TeachingResponse {
  strategy: TeachingStrategy;
  messages: string[];
  follow_up: string | null;
  visual: string | null;
  key_idea: string;
  ready_for_transfer: boolean;
}

export interface PublicQuestion {
  id: string;
  concept: string;
  prompt: string;
  emoji: string;
  source: "authored" | "generated" | "teach_back";
}

export interface QuestionQuality {
  same_concept: boolean;
  age_appropriate: boolean;
  answerable: boolean;
  curriculum_aligned: boolean;
  not_a_repeat: boolean;
  difficulty: "easier" | "similar" | "harder";
  approved: boolean;
  notes: string[];
}

export interface MasteryChange {
  concept_id: string;
  concept_name: string;
  before: number;
  after: number;
  evidence: number;
  reason: string;
}

export interface TraceStep {
  key: string;
  step: string;
  status: "complete" | "skipped" | "fallback" | "error";
  mode: StepMode;
  duration_ms: number;
  summary: string;
  output: Record<string, unknown>;
}

export interface SafetyNotice {
  category: "pii" | "unsafe" | "prompt_injection" | "off_topic" | "answer_request" | "language";
  message: string;
  redactions: string[];
}

export interface StateTransition {
  from_phase: LearningPhase;
  to_phase: LearningPhase;
  trigger: string;
  at: string;
}

export interface LearningState {
  concept_id: string;
  concept_name: string;
  phase: LearningPhase;
  classification: Classification | null;
  misconception_id: string | null;
  misconception_label: string | null;
  intervention: TeachingStrategy | null;
  mastery: number;
  mastery_status: string;
  transfer_attempts: number;
  deferred_reason: string | null;
  history: StateTransition[];
}

/** When `blocked` is true only `safety`, `trace` and `trace_id` are present. */
export interface SubmitResponse {
  interaction_id: string | null;
  trace_id: string;
  mode: string;
  blocked: boolean;
  safety: SafetyNotice | null;
  learning_state: LearningState | null;
  verification: Verification | null;
  diagnosis: Diagnosis | null;
  feedback: AnalysisFeedback | null;
  teaching_strategy: TeachingStrategy | null;
  strategy_reason: string;
  teaching_response: TeachingResponse | null;
  transfer_question: PublicQuestion | null;
  question_quality: QuestionQuality | null;
  mastery_before: number | null;
  mastery_after: number | null;
  mastery_change: MasteryChange | null;
  trace: TraceStep[];
  transfer_demo_answer: string;
}

export interface ReplyResponse {
  interaction_id: string;
  turn: number;
  resolved: boolean;
  ready_for_transfer: boolean;
  deferred: boolean;
  blocked: boolean;
  safety: SafetyNotice | null;
  learning_state: LearningState | null;
  analysis: AnalysisFeedback | null;
  teaching_response: TeachingResponse;
  trace: TraceStep[];
}

export interface TransferResponse {
  interaction_id: string;
  trace_id: string;
  blocked: boolean;
  safety: SafetyNotice | null;
  learning_state: LearningState | null;
  next_state: "mastered" | "verified" | "reteach" | "revisit";
  mastery_confirmed: boolean;
  mastery_before: number | null;
  mastery_after: number | null;
  mastery_change: MasteryChange | null;
  concept_status: MasteryStatus | null;
  feedback: string;
  verification: Verification | null;
  teaching_response: TeachingResponse | null;
  next_transfer_question: PublicQuestion | null;
  next_transfer_demo_answer: string;
  attempt: number;
  xp_earned: number;
  trace: TraceStep[];
}

export interface MisconceptionStat {
  id: string;
  label: string;
  statement: string;
  topic_id: string;
  topic_name: string;
  concept_id: string;
  concept_name: string;
  students: number;
  occurrences: number;
  resolved_rate: number;
}

export interface ClassAnalytics {
  class_name: string;
  students: number;
  questions_answered: number;
  verified_mastery_rate: number;
  avg_mastery: number;
  active_today: number;
  answer_vs_reasoning: Record<string, number>;
  top_misconceptions: MisconceptionStat[];
  topics: { topic_id: string; name: string; color: string; emoji: string; avg_mastery: number; mastered: number; learning: number; needs_practice: number }[];
  strategies: { strategy: TeachingStrategy; uses: number; success_rate: number }[];
  activity: { date: string; answers: number; verified: number }[];
  heatmap_concepts: { id: string; name: string; topic_id: string }[];
  roster: {
    id: string;
    display_name: string;
    avatar: string;
    avg_mastery: number;
    answered: number;
    verified: number;
    top_misconception: string | null;
    scores: Record<string, number>;
  }[];
  classification_mix: Record<string, number>;
  safety_events: Record<string, number>;
  open_reviews: number;
  loop_outcomes: Record<string, number>;
}

export interface TraceSummary {
  id: string;
  interaction_id: string;
  student_id: string;
  student_name: string;
  avatar: string;
  topic_id: string;
  concept_id: string;
  concept_name: string;
  question_prompt: string;
  answer: string;
  answer_correct: boolean | null;
  reasoning_correct: boolean | null;
  misconception_label: string | null;
  strategy: TeachingStrategy | null;
  mastery_before: number | null;
  mastery_after: number | null;
  transfer_confirmed: boolean | null;
  mode: string;
  total_ms: number;
  created_at: string;
}

export interface TraceDetail extends TraceSummary {
  verification: Partial<Verification>;
  diagnosis: Partial<Diagnosis>;
  feedback: Partial<AnalysisFeedback>;
  teaching: Partial<TeachingResponse> & { reason?: string };
  dialogue: { role: "student" | "curio"; text: string; strategy: string | null }[];
  transfer_question: { id: string; prompt: string; emoji: string; source: string } | null;
  transfer_answer: string | null;
  transfer_feedback: string | null;
  transfer_verification: Partial<Verification> | null;
  final_mastery: number | null;
  steps: TraceStep[];
  transfer_steps: TraceStep[];
  learning_state: LearningState | null;
  transfer_attempts: {
    attempt: number;
    prompt: string;
    source: string;
    answer: string;
    confirmed: boolean;
    feedback: string;
    mastery_before: number | null;
    mastery_after: number | null;
  }[];
}

export interface ReviewItem {
  id: string;
  kind: "safety" | "deferred" | "persistent_misconception" | "stuck";
  category: string;
  severity: "high" | "medium" | "low" | "none";
  student_id: string;
  student_name: string;
  avatar: string;
  question_id: string | null;
  question_prompt: string | null;
  excerpt: string;
  status: "open" | "resolved";
  note: string;
  created_at: string;
}

export interface Pathway {
  id: string;
  theme: string;
  topic_id: string;
  topic_name: string;
  concept_id: string;
  concept_name: string;
  learning_objective: string;
  diagnostic_question: string;
  expected_explanation: string;
  reasoning_points: string[];
  required_points: string[];
  misconceptions: MisconceptionCard[];
  hints: string[];
  transfer_questions: { id: string; prompt: string; expected_answer: string; reasoning: string[] }[];
  mastery_criterion: string;
  review_status: "draft" | "approved" | "flagged";
  reviewer: string | null;
  review_note: string;
  reviewed_at: string | null;
}

export interface PrivacySummary {
  student_id: string;
  stored: Record<string, number>;
  retention_days: number;
  data_categories: string[];
  not_collected: string[];
}

export interface EvalCase {
  id: string;
  split: "dev" | "test";
  question_id: string;
  category: string;
  answer: string;
  gold: { classification: Classification; misconception_id?: string; answer_correct?: boolean; safety: string };
  pred: { classification: Classification; misconception_id: string | null; safety: string; strategy: string | null; baseline_credit: boolean };
  consistent: boolean;
  match: boolean;
}

export interface EvalSplit {
  cases: number;
  classification_accuracy: number | null;
  safety_catch_rate: number | null;
  curio_false_mastery_rate: number | null;
  baseline_false_mastery_rate: number | null;
}

export interface EvalReport {
  generated_at: string;
  mode: string;
  benchmark: { path: string; version: number; labeller: string; cases: number };
  metrics: Record<string, number | null>;
  understanding_gate: Record<string, number | null>;
  by_split: { dev: EvalSplit; test: EvalSplit };
  per_class: Record<string, { support: number; precision: number | null; recall: number | null; f1: number }>;
  confusion: Record<string, Record<string, number>>;
  safety: Record<string, { cases: number; caught: number }>;
  by_category: Record<string, { cases: number; accuracy: number | null }>;
  cases: EvalCase[];
}
