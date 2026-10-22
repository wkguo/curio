# LLM-only baseline vs Curio

Generated 2026-10-22T13:36:15.193663+00:00 · model `curio-qwen27b` · 24 cases · labels: Draft gold labels (AI-drafted, pending teacher review)

The LLM-only baseline gets the same curriculum key and similar safeguards in a single prompt, but no safety layer,
no rule reconciliation and no evidence gate. Each cell: all cases · held-out test split (historical safety caveat below).
Rows the model failed to answer are excluded from every rate (see 'answered').
False mastery is a single-response proxy against draft labels, not evidence of learning gains or mastery after teaching.

| Metric | Curio (rules only) | Curio + LLM | LLM only (one prompt) |
|---|---|---|---|
| Cases answered by the system | 100.0% · test 100.0% | 100.0% · test 100.0% | 100.0% · test 100.0% |
| Classification accuracy | 79.2% · test 50.0% | 62.5% · test 37.5% | 79.2% · test 62.5% |
| Safety & privacy catch rate | 100.0% · test 100.0% | 100.0% · test 100.0% | 100.0% · test 100.0% |
| False mastery (response does not show understanding) ↓ | 7.1% · test 16.7% | 7.1% · test 16.7% | 0.0% · test 0.0% |
| False mastery on right answer + poor reasoning ↓ | 16.7% · test 50.0% | 16.7% · test 50.0% | 0.0% · test 0.0% |
| Credit given to fully correct responses ↑ | 100.0% · test 100.0% | 100.0% · test 100.0% | 100.0% · test 100.0% |
| First reply already states every key point, not-understood responses ↓ | 7.1% · test 16.7% | 35.7% · test 50.0% | 14.3% · test 16.7% |
| First reply already states every key point, answer requested ↓ | n/a · test n/a | n/a · test n/a | n/a · test n/a |
| Regex-detectable personal data sent to the provider (by design) ↓ | n/a · test n/a | 0.0% · test n/a | 100.0% · test n/a |
| Same decision on a second run ↑ | 100.0% · test 100.0% | 100.0% · test 100.0% | 100.0% · test 100.0% |
| Model calls | 0 | 153 | 48 |
| Model failures | 0 first-pass, 0 repeat | 0 first-pass, 0 repeat, 0.0% steps fell back | 0 first-pass, 0 repeat |

Denominators, held-out test: not-understood 6, safety 1, poor reasoning 2, answer requests 0, PII 0. Small numbers: treat differences of a few points as noise. The give-away rows are a keyword match, not a judge.
Historical caveat: one earlier safety-rule change used a held-out example; safety catch rates are optimistic. Labels are AI-drafted, awaiting teacher review.
