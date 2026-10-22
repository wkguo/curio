# LLM-only baseline vs Curio

Generated 2026-10-22T14:39:15.825648+00:00 · model `curio-qwen27b` · 121 cases · labels: Draft gold labels (AI-drafted, pending teacher review)

The LLM-only baseline gets the same curriculum key and similar safeguards in a single prompt, but no safety layer,
no rule reconciliation and no evidence gate. Each cell: all cases · held-out test split (historical safety caveat below).
Rows the model failed to answer are excluded from every rate (see 'answered').
False mastery is a single-response proxy against draft labels, not evidence of learning gains or mastery after teaching.

| Metric | Curio (rules only) | Curio + LLM | LLM only (one prompt) |
|---|---|---|---|
| Cases answered by the system | 100.0% · test 100.0% | 100.0% · test 100.0% | 100.0% · test 100.0% |
| Classification accuracy | 78.5% · test 60.0% | 55.4% · test 40.0% | 81.0% · test 75.0% |
| Safety & privacy catch rate | 86.4% · test 57.1% | 86.4% · test 57.1% | 100.0% · test 100.0% |
| False mastery (response does not show understanding) ↓ | 4.8% · test 6.9% | 1.2% · test 3.5% | 0.0% · test 0.0% |
| False mastery on right answer + poor reasoning ↓ | 16.7% · test 16.7% | 5.6% · test 16.7% | 0.0% · test 0.0% |
| Credit given to fully correct responses ↑ | 100.0% · test 100.0% | 100.0% · test 100.0% | 100.0% · test 100.0% |
| First reply already states every key point, not-understood responses ↓ | 15.7% · test 20.7% | 25.3% · test 34.5% | 9.6% · test 6.9% |
| First reply already states every key point, answer requested ↓ | 0.0% · test 0.0% | 0.0% · test 0.0% | 0.0% · test 0.0% |
| Regex-detectable personal data sent to the provider (by design) ↓ | n/a · test n/a | 0.0% · test 0.0% | 100.0% · test 100.0% |
| Same decision on a second run ↑ | 100.0% · test 100.0% | 94.2% · test 100.0% | 96.7% · test 95.0% |
| Model calls | 0 | 864 | 242 |
| Model failures | 0 first-pass, 0 repeat | 0 first-pass, 0 repeat, 0.9% steps fell back | 0 first-pass, 0 repeat |

Denominators, held-out test: not-understood 29, safety 7, poor reasoning 6, answer requests 1, PII 1. Small numbers: treat differences of a few points as noise. The give-away rows are a keyword match, not a judge.
Historical caveat: one earlier safety-rule change used a held-out example; safety catch rates are optimistic. Labels are AI-drafted, awaiting teacher review.
