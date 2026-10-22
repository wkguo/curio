import {
  Eye,
  FlaskConical,
  HelpCircle,
  Layers,
  Lightbulb,
  MessageCircleQuestion,
  Repeat,
  Shapes,
  type LucideIcon,
} from "lucide-react";

import type { Classification, LearningPhase, MasteryStatus, MisconceptionType, TeachingStrategy } from "@/types/api";

export const STRATEGY: Record<TeachingStrategy, { label: string; icon: LucideIcon; blurb: string; tone: string }> = {
  DIRECT_HINT: { label: "Direct Hint", icon: Lightbulb, blurb: "A small, clear nudge in the right direction.", tone: "bg-sun-100 text-sun-700" },
  SOCRATIC_QUESTION: { label: "Socratic Question", icon: MessageCircleQuestion, blurb: "Guiding questions so the student finds the step.", tone: "bg-sky-100 text-sky-700" },
  ANALOGY: { label: "Analogy", icon: Shapes, blurb: "An everyday comparison that makes the idea click.", tone: "bg-curio-100 text-curio-700" },
  COUNTEREXAMPLE: { label: "Counterexample", icon: FlaskConical, blurb: "A situation where the wrong idea predicts the wrong thing.", tone: "bg-coral-100 text-coral-700" },
  SIMPLER_EXPLANATION: { label: "Simpler Explanation", icon: HelpCircle, blurb: "The core idea, said very simply.", tone: "bg-mint-100 text-mint-700" },
  PREREQUISITE_REVIEW: { label: "Prerequisite Review", icon: Layers, blurb: "Refresh the building-block idea first.", tone: "bg-ink-100 text-ink-700" },
  VISUAL_EXPLANATION: { label: "Visual Explanation", icon: Eye, blurb: "A picture of what is happening.", tone: "bg-sky-100 text-sky-700" },
  TRANSFER_EXAMPLE: { label: "Transfer Example", icon: Repeat, blurb: "Understanding verified — try a new situation.", tone: "bg-mint-100 text-mint-700" },
  CLARIFY: { label: "Clarify First", icon: MessageCircleQuestion, blurb: "Not enough evidence yet — ask before teaching anything.", tone: "bg-ink-100 text-ink-700" },
};

export const PHASE: Record<LearningPhase, { label: string; emoji: string; tone: string }> = {
  attempt: { label: "Attempt", emoji: "pencil", tone: "bg-ink-100 text-ink-600" },
  blocked: { label: "Paused by safety layer", emoji: "warning", tone: "bg-sun-100 text-sun-700" },
  clarifying: { label: "Clarifying", emoji: "thinking_face", tone: "bg-ink-100 text-ink-700" },
  teaching: { label: "Teaching", emoji: "light_bulb", tone: "bg-curio-100 text-curio-700" },
  transfer: { label: "Question back", emoji: "rocket", tone: "bg-sky-100 text-sky-700" },
  reteach: { label: "Re-teaching", emoji: "books", tone: "bg-sun-100 text-sun-700" },
  mastered: { label: "Mastered", emoji: "trophy", tone: "bg-mint-100 text-mint-700" },
  verified: { label: "Verified", emoji: "check_mark_button", tone: "bg-mint-100 text-mint-700" },
  revisit: { label: "Revisit later", emoji: "seedling", tone: "bg-coral-100 text-coral-700" },
  deferred: { label: "Teacher review", emoji: "teacher", tone: "bg-sky-100 text-sky-700" },
};

export const CLASSIFICATION: Record<Classification, { label: string; tone: string }> = {
  correct: { label: "Correct", tone: "bg-mint-100 text-mint-700" },
  incomplete: { label: "Incomplete", tone: "bg-sun-100 text-sun-700" },
  misconception: { label: "Misconception", tone: "bg-coral-100 text-coral-700" },
  incorrect: { label: "Incorrect", tone: "bg-coral-50 text-coral-600" },
  unclear: { label: "Unclear", tone: "bg-ink-100 text-ink-600" },
  guess: { label: "Guess", tone: "bg-ink-100 text-ink-500" },
  blocked: { label: "Blocked (safety)", tone: "bg-sky-100 text-sky-700" },
};

export const SAFETY_LABEL: Record<string, string> = {
  none: "None",
  pii: "Personal data",
  unsafe: "Wellbeing concern",
  prompt_injection: "Prompt injection",
  off_topic: "Off-topic",
  answer_request: "Answer request",
  language: "Not English",
};

export const MISCONCEPTION_TYPE: Record<MisconceptionType, string> = {
  FACTUAL_ERROR: "Factual error",
  CAUSAL_ERROR: "Causal error",
  CONCEPT_CONFUSION: "Concept confusion",
  MISSING_STEP: "Missing step",
  OVERGENERALIZATION: "Overgeneralization",
  VOCABULARY_CONFUSION: "Vocabulary confusion",
  CORRECT_BUT_INCOMPLETE: "Correct but incomplete",
  GUESS_WITHOUT_REASONING: "Guess without reasoning",
};

// Status palette — reserved for mastery state; always paired with an icon + label.
export const STATUS: Record<MasteryStatus, { label: string; color: string; soft: string; text: string; ring: string }> = {
  mastered: { label: "Mastered", color: "#1FB978", soft: "bg-mint-50", text: "text-mint-700", ring: "ring-mint-200" },
  learning: { label: "Learning", color: "#F5A70A", soft: "bg-sun-50", text: "text-sun-700", ring: "ring-sun-200" },
  needs_practice: { label: "Needs practice", color: "#FF6B3D", soft: "bg-coral-50", text: "text-coral-700", ring: "ring-coral-200" },
  new: { label: "Ready to start", color: "#7C5CFF", soft: "bg-curio-50", text: "text-curio-700", ring: "ring-curio-200" },
  locked: { label: "Locked", color: "#C9C7D8", soft: "bg-ink-50", text: "text-ink-500", ring: "ring-ink-200" },
};

export const MODE_LABEL: Record<string, string> = { llm: "LLM", rules: "Curriculum rules", fallback: "Safe fallback" };
