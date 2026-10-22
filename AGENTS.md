# Curio — agent guide

Map, not manual. Details: [README.md](README.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/DESIGN.md](docs/DESIGN.md).

## Commands (run before claiming done)
- `make test` — pytest + curriculum linter + `tsc --noEmit`
- `make build` — Next.js production build
- `make eval` — benchmark report (backend/evaluation/reports/latest.md)
- `make eval-llm-baseline` — one-prompt LLM vs Curio on the same benchmark (needs an LLM key; costs tokens)
- `make fixtures` — REQUIRED after any change to API shapes, harness output or curriculum (offline demo replays these)

## Invariants (enforced by tests — don't weaken the test, fix the cause)
- Scripted demo: Alex heat_conduction 0.52 → 0.56 (submit) → 0.76 (transfer). `tests/test_demo_flow.py`.
- Grading keys (`expected_answer`, reasoning patterns) never leave the server; the client gets `PublicQuestion` only.
- Harness failure → `503 curio_unavailable` + friendly message; never stack traces / raw prompts.
- Misconception text never earns reasoning credit (verifier blocks misconception spans).
- Teaching dialogue is bounded (`MAX_TURNS = 2`); transfer regeneration happens at most once; at most 2 transfer attempts (`MAX_TRANSFER_ATTEMPTS`).
- Repeated "I don't know" is bounded: once a failed transfer makes `DONT_KNOW_LIMIT` (3) don't-knows in a row, the question ends (key idea shown, `revisit`, teacher queue item `stuck`), never a second question; it never changes mastery.
- Safety layer runs first on every student message; only redacted text is stored or sent to a model.
- "Mastered" requires a verified transfer (`status_for(..., verified)`); a bare answer without explanation is never `correct`.
- Learning-state changes go through `harness.state.transition` (invalid transitions raise).
- Evaluation: never tune rules on `split == "test"` benchmark cases (every 3rd id); report dev and test separately.

## Conventions
- Backend: one module per harness step; each returns `(result, mode)` where mode ∈ llm|rules|fallback.
- Curriculum YAML: quote any string containing `: `; emoji keys must exist in `frontend/public/assets/emoji/`.
- Frontend types in `frontend/types/api.ts` mirror `backend/schemas/api.py` — change both together.
- Status colors (mint/sun/coral) are reserved for mastery state and always paired with an icon + label.
