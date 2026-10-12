# Demo script (≈ 4 minutes)

**Setup:** run `make dev`, open http://localhost:3000, and click **Reset demo** in the sidebar's student switcher. Keep `CURIO_HARNESS_MODE=rules` for a fully deterministic run.

| # | Where | Say | Do |
|---|---|---|---|
| 1 | `/` | "Chatbots give answers. Curio checks understanding." | Point at the hero card: *answer ✓, reasoning ✗*. |
| 2 | `/dashboard` | "This is Alex, Primary 5. Heat Transfer is at 56%, and Heat Conduction is only half understood." | Click **Continue Learning**. |
| 3 | `/learn` Q1 | "Alex gives the classic answer." | Click **🤔 Alex's answer**, then **Submit**. |
| 4 | Thinking | "Curio verifies the reasoning, not just the answer." | Let the five steps tick. |
| 5 | Analysis | "The final answer is right (metal *does* feel colder), but the reasoning is wrong. Curio quotes Alex's own claim back." | Point at ✓ / ⚠. |
| 6 | Teaching | "It's a causal error, so the policy picks a **counterexample**. Curio doesn't reveal the answer; it asks a question." | Hover the strategy chip to show the reason. |
| 7 | Dialogue | "Alex reasons toward it himself." | Click **💡 Alex's idea**, then **Reply**. The idea is repaired. |
| 8 | Transfer | "Now the real test: the same idea in a new situation." | Click **Take the transfer challenge**, then **✨ Alex's answer**. |
| 9 | Result | "Understanding verified. Mastery 52 → 76%." | Show the confetti and the right panel's bar updating. |
| 10 | Trace | "Every decision is inspectable." | Click **See how Curio decided**, then click the *Misconception* and *Teaching strategy* nodes to show the JSON. |
| 11 | `/teacher` | "Across the class, many correct answers hid a reasoning gap a normal quiz would miss." | Show the answer-vs-reasoning bar, top misconceptions, strategy effectiveness and the heatmap. |
| 12 | `/progress` | "Mastery drives the concept map: what's mastered, what's next, what's locked." | Click a node. |

## Add-on: the proposal's controls (≈ 2 minutes)

| # | Where | Say | Do |
|---|---|---|---|
| 13 | `/learn` Q2 | "Curio never just hands over answers…" | Type `just tell me the answer` → a hint, nothing graded. |
| 14 | `/learn` Q2 | "…and it doesn't teach when it can't tell what the child means." | Type `the ice does something to the juice` → **Clarify first**. Reply with a real idea → re-assessed. |
| 15 | `/learn` | "Mastery is a gate, not a score." | Give a strong answer, then fail the transfer (`metal is colder`) → **re-teach + a second question back**. The right panel shows the explicit state transitions. |
| 16 | `/teacher` | "The AI knows when to hand over to a human." | Open *Needs your attention*: deferred answers, persistent misconceptions, safety flags. |
| 17 | `/teacher/content` | "Every pathway is teacher-reviewed before use." | Expand a pathway and approve it. |
| 18 | `/teacher/evaluation` | "We measure it. On held-out cases an answer-only grader wrongly credits mastery 48% of the time; Curio 14%. And we show where the rules overfit." | Show the gate bars and the dev-vs-test table. |
| 19 | `/privacy` | "Children's data: kept minimal, visible, deletable." | Show the inventory and the delete button. |

**Backup:** if the backend fails mid-demo, the app switches to *Offline demo* on its own (the yellow badge) and keeps working from recorded data.
