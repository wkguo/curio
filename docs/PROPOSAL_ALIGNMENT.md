# GP8001 proposal → implementation map

Source: [`docs/source/GP8001_Curio_Proposal_B3.docx`](source/GP8001_Curio_Proposal_B3.docx). This file shows where each commitment in the proposal lives in the code, and how it is verified.

## Core loop

> STUDENT ATTEMPT → VERIFY → VALIDATE → TEACH → QUESTION BACK → MASTERY CHECK

| Proposal | Implementation | Verified by |
|---|---|---|
| Explicit state transition after each attempt; compact learning state (concept, misconception, intervention, mastery status) | `harness/state.py` (`LearningState`, `ALLOWED` transition table, `InvalidTransition`). The state is stored with every interaction and returned by every learning API call | `test_failed_transfer_reteaches_then_asks_a_second_question` asserts the exact transition history; `test_invalid_state_transition_is_rejected` |
| Mastery checker either advances the student or re-enters teaching | `PedagogicalHarness.run_transfer`: when a transfer fails → re-teach + a second question back (the next authored one, or a *teach-back* prompt), bounded to 2 attempts → `revisit` | same test; the UI shows the reteach loop |
| Mastery requires evidence of explanation or application | `mastery.status_for(..., verified)`: *mastered* needs score ≥ 0.75 **and** ≥ 1 verified transfer. `require_explanation()`: a bare answer with no "because" can never be classed *correct*. A misconception in a transfer answer earns no positive evidence | `test_mastery_requires_transfer_evidence`, `test_misconception_on_transfer_earns_no_mastery` |
| If evidence is insufficient, ask for clarification or defer to teacher review instead of an unverified explanation | Classification `unclear` → strategy `CLARIFY` (no science content taught). Re-assessment after the clarification. Still unclear after 2 turns → `deferred` plus an item in the teacher queue | `test_unclear_answer_asks_for_clarification_without_teaching`, `test_clarification_that_reveals_a_misconception_moves_to_teaching`, `test_still_unclear_after_clarification_is_deferred_to_teacher` |

## Six modules (proposal table)

| # | Proposal module | Code |
|---|---|---|
| 1 | Student-response analyser (answer, explanation, stated reasoning, uncertainty) | `harness/problem_parser.py` returns `answer_part`, `explanation_part`, `has_explanation` and `uncertainty_markers` |
| 2 | Curriculum retriever (Theme / Topic / LO / Concept + expected explanation + misconceptions) | `curriculum/retriever.py`. Packs carry `theme`, `syllabus_ref` and per-concept `mastery_criterion` |
| 3 | Reasoning & misconception checker (correct / incomplete / misconception-linked) | `harness/verifier.py` emits `classification` ∈ correct · incomplete · misconception · incorrect · unclear · guess (blocked comes from the safety layer). Misconception text can never earn reasoning credit |
| 4 | Response planner + LLM (generation follows the decision) | `harness/teaching_policy.py` (pure decision) → `harness/teaching_agent.py`. Curated content comes first; the LLM only words the chosen action, and its output passes the output guard |
| 5 | Transfer / mastery checker | `run_transfer` plus `harness/mastery.py` evidence rules plus the state machine |
| 6 | Safety / privacy layer | `harness/safety.py`. Runs first on every message: PII redaction (phone, email, NRIC/FIN, address and postal code; only the *kind* is stored), wellbeing concerns (stop grading, show helplines, high-severity teacher alert), prompt injection, off-topic chat, "just give me the answer". `check_output()` guards LLM output (PII, unsafe, out-of-syllabus vocabulary) |

## Knowledge base and teacher review

| Proposal | Implementation |
|---|---|
| Hierarchy Theme → Topic → LO → Concept → Expected Explanation → Misconception → Diagnostic Q → Follow-up Q → Mastery Criterion | YAML packs in `backend/curriculum/data/`, exposed as `Pathway` (`GET /api/teacher/pathways`) |
| ~20–30 concept pathways with the same structured fields | **24 pathways** (8 per topic), **48 transfer questions** (2 per pathway), 16 misconceptions. `scripts/check_curriculum.py` enforces the fields |
| Each pathway teacher-reviewed before use | `/teacher/content`: approve / flag / note per pathway (`content_reviews` table). `CURIO_REQUIRE_REVIEWED_CONTENT=true` serves only approved pathways (HTTP 409 with a friendly message otherwise). Every pathway starts as **draft**, because none has been reviewed by a real teacher yet |
| P5–P6 scope | Packs are labelled Primary 5–6. Note: in the MOE syllabus, heat and states of matter are mainly P4 content. The P5–P6 framing is a product choice for a teacher to confirm |

## Privacy (PDPC Advisory Guidelines on children's personal data)

- Data minimisation: answers are stored **after** redaction. Blocked messages store only the redacted text and the category.
- Transparency: `/privacy` and `GET /api/privacy/students/{id}` list what is kept, what is never collected, and record counts.
- Deletion: `DELETE /api/privacy/students/{id}`. Retention: `CURIO_RETENTION_DAYS` with `POST /api/privacy/purge`.
- Traces store structured step outputs only, never raw prompts.

## Evaluation (proposal §Evaluation and Validation)

- `backend/evaluation/benchmark.yaml`: **121 gold-labelled cases** in the proposal's buckets: correct, correct-but-poor-reasoning, incomplete, misconception, ambiguous, guess, and safety (PII, wellbeing, injection, off-topic, answer requests). The labels were drafted *without* looking at Curio's regex patterns, and are marked "pending teacher review".
- `make eval` (or `/teacher/evaluation` → *Re-run*) scores the real harness on:
  - classification, misconception recall and precision, answer agreement;
  - safety catch rate and false alarms;
  - decision consistency;
  - **an answer-only baseline** (what an auto-marked quiz does), measured as the *false-mastery rate*.
- **Dev / held-out split**: every third case is never inspected while the rules are improved.

Latest rules-mode results (`backend/evaluation/reports/latest.md`):

| | Dev (81) | Held-out test (40) |
|---|---|---|
| Classification accuracy | 87.7% | **60.0%** |
| Safety catch rate | 100% | **42.9%** |
| False mastery: Curio vs answer-only baseline | 3.7% vs 51.9% | **13.8% vs 48.3%** |

Interpretation:
1. The verification gate cuts false mastery by about 3.5× on unseen cases. This is the result the research question asks for.
2. The hand-written patterns overfit: the dev score is far above the held-out score. Safety pattern matching in particular does not generalise to unseen wording. Per the proposal's phase-4 decision gate, an LLM-based safety classifier and the LLM verifier (`CURIO_HARNESS_MODE=llm`) should be added and re-benchmarked before any pilot with children.
3. The benchmark labels are AI-drafted. Teacher review of the gold labels is the next step (proposal phase 5).
