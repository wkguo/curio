# Curio architecture

## 1. The harness: one orchestrator, many small steps

`backend/harness/orchestrator.py` runs every step in order and records each one as a `TraceStep` (`key`, `status`, `mode`, `duration_ms`, `summary`, `output`). As spec §5 requires, the steps are plain async functions. None of them is an autonomous agent.

| # | Step | Module | Rule path (always available) | LLM path (when configured) |
|---|---|---|---|---|
| 1 | Curriculum Retrieval | `curriculum/retriever.py` | Look up the concept, prerequisites and candidate misconceptions | — |
| 2 | Problem Parsing | `harness/problem_parser.py` | Normalise the answer, cap its length, detect guesses | — |
| 3 | Reference Solution | `harness/reference_solver.py` | Teacher-authored answer key | Only when a question has no key |
| 4 | Reasoning Verification | `harness/verifier.py` | Regex evidence for each reasoning point and misconception | Structured `Verification`, **reconciled** with the rule result |
| 5 | Misconception Diagnosis | `harness/misconception.py` | Choose the single most severe gap, check the student's history for repeats | Only for *novel* misconceptions the pack doesn't name |
| 6 | Teaching Strategy | `harness/teaching_policy.py` | Heuristic policy (spec §8) plus prerequisite check plus rotation on repeats | — (the seam for a learned policy) |
| 7 | Teaching Response | `harness/teaching_agent.py` | Authored block for (misconception, strategy), else a template | Generated when no authored block exists |
| 8 | Transfer Question | `harness/question_generator.py` | Next authored transfer question the student hasn't seen | Generate → verify → regenerate once → authored fallback |
| 9 | Question Quality Check | `harness/question_verifier.py` | Same concept, readability, scope, safety, not a repeat | LLM reviewer as a second opinion |
| 10 | Mastery Update | `harness/mastery.py` | `m + 0.2 × evidence`, clamped to [0, 1] | — |

The **teaching dialogue** (`harness/dialogue.py`) checks each reply against the misconception's `resolution_patterns` or against the missing reasoning points. It is **bounded**: after 2 turns Curio states the key idea and moves on to the transfer question. A short "I don't know" gets the next rung of help instead of "getting closer" (hint, then the key idea). If the student is still saying "I don't know" at the transfer question (`DONT_KNOW_LIMIT` = 3 in a row), Curio explains the answer, ends the question as *revisit* and puts a `stuck` item in the teacher queue instead of asking a second question.

## 2. Key decisions

**Curated content before generated content.** Children are the audience. When a teacher-authored teaching block exists for the diagnosed misconception, it wins over LLM text. The LLM covers gaps: novel misconceptions, missing-step coaching and fresh transfer questions. Everything it generates goes through a validated schema, and generated questions also go through the quality verifier.

**The LLM verifier is reconciled, not trusted blindly.** If the model misses a misconception the curriculum pack detects, the known misconception is added back and `reasoning_correct` is forced to false. Reasoning-point IDs the model invents are dropped. This keeps the demo deterministic and the diagnosis auditable, even in LLM mode.

**Misconception text never earns reasoning credit.** The rule verifier blocks every text span that matches a misconception pattern before it scores reasoning points. For example, "it needs a force *to keep moving*" can't earn the "keeps moving on its own" point. A regression test covers every question in every pack.

**Correct answer ≠ mastery.** Mastery evidence follows spec §11 exactly:

| Evidence | Case |
|---|---|
| **+1.0** | Transfer success (answer and reasoning correct in a new context) |
| +0.5 | Correct answer + correct reasoning |
| +0.2 | Partial (right answer with flawed reasoning, or some reasoning points) |
| 0.0 | Guess / no evidence |
| −0.1 | Repeated misconception |

With a learning rate of 0.2, the scripted demo gives 0.52 → 0.56 → 0.76. The tests pin these numbers.

**Failure contract (spec §25).**
1. Structured output is retried once, with the validation error fed back to the model.
2. A tolerant JSON extractor then handles code fences and surrounding prose.
3. If that also fails, the step falls back to its rule path and the trace records `status="fallback"`.
4. If the orchestrator itself crashes, the API returns `503 curio_unavailable` with the friendly message. It never returns a stack trace.

**Rules have guards against the failures found by fuzzing the demo (2026-10-22).** A misconception match the student explicitly denies ("wool doesn't make heat") is not flagged; apostrophe-free contractions ("dont") are normalised before matching; "I don't know" is recognised as a phrase plus filler, so "not sure, metal is colder" still counts as an attempt; text in another script gets a "please use English" notice instead of being graded. Harm statements need intent ("how do I hurt my brother"), so "hurt my fingers" is not a wellbeing alert.

**Retention.** Records older than `CURIO_RETENTION_DAYS` (365) are purged at every server start, including the teacher-queue excerpts; `POST /api/privacy/purge` does the same on demand. A scheduled job is a pre-pilot item.

**The grading key never reaches the client.** `GeneratedQuestion` (which contains the expected answer) stays server-side. The client receives only `PublicQuestion`.

**No raw prompts in traces.** Traces store each step's structured *output* only. Prompts live in `backend/prompts/*.txt` and are rendered server-side.

## 3. Data model (SQLite)

`students`, `concepts`, `questions` (including generated ones and their grading keys), `student_mastery`, `mastery_events` (for trend charts), `learning_sessions`, `student_responses` (kinds: `initial`, `dialogue`, `transfer`, linked by `parent_id`), and `agent_traces`.

A learning interaction is one `initial` response with its `dialogue` and `transfer` children. The teacher trace view reassembles the whole story from that tree.

## 4. Curriculum packs

`curriculum/data/*.yaml` is validated by `schemas/curriculum.py` at startup: every regex must compile and every ID must resolve. `scripts/check_curriculum.py` adds authoring checks:
- demo answers are self-consistent;
- the prerequisite graph has no cycles;
- emoji keys exist as frontend assets;
- no list item was silently parsed as a YAML dict.

To add a topic:
1. Copy `heat_transfer.yaml`.
2. Run `uv run python scripts/check_curriculum.py`.
3. Add the topic ID to `TOPIC_ORDER` in `curriculum/loader.py`.
4. Regenerate fixtures with `make fixtures`.

## 5. Frontend data flow

`lib/api.ts` calls `/api/*`, which the Next.js rewrite proxies to FastAPI. When the backend is unreachable, the client switches to offline mode and serves `public/mock/fixtures.json`. A small overlay keeps mastery bars moving during an offline demo.

The learning page (`components/learn/learning-session.tsx`) is a phase machine:
`answer → thinking → teaching ⇄ (reply) → ready → transfer → verifying → result`.
The thinking animation waits for two things: the request to finish *and* every step to have been shown. Fast responses still read well, and slow ones never stall on a fake 100%.

## 6. Extension points

- **Learned teaching policy**: replace `select_strategy(diagnosis, snapshot, ctx)`. Its inputs and outputs are already typed, and `/api/analytics/class` reports how well each strategy works.
- **Richer student model**: `harness/mastery.py` is pure. Swap in BKT or IRT behind the same `initial_evidence`, `transfer_evidence` and `update` functions.
- **Multimodal (P2)**: `ProblemParser` is the entry point for OCR, images and voice transcripts.
- **Model provider**: implement `LLMClient.generate(messages, schema)`.
