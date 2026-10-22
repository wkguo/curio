"""Benchmark evaluation (proposal §Evaluation and Validation).

Runs every case in evaluation/benchmark.yaml through the REAL harness and scores it
against the gold labels:

* response classification (correct / incomplete / misconception / incorrect / unclear / guess / blocked)
* misconception detection (recall / precision on misconception ids)
* answer-correctness agreement
* safety & privacy catch rate per category, and false alarms on normal answers
* decision consistency (each case is run twice; identical decisions expected)
* **baseline comparison** — an answer-only grader (what a typical quiz does) vs Curio, measured
  as the *false-mastery rate*: how often a response that does NOT show understanding would be
  credited as mastered.

    uv run python -m evaluation.run            # rules mode (deterministic)
    uv run python -m evaluation.run --mode llm # uses the configured LLM

Writes evaluation/reports/latest.json and latest.md.
"""

import argparse
import asyncio
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from curriculum.loader import get_curriculum
from harness.context import GradingKey, StudentSnapshot
from harness.orchestrator import BlockedResult, PedagogicalHarness
from harness.problem_parser import parse_problem
from harness.text import matches
from services.llm import DisabledLLMClient, LLMClient, get_llm

HERE = Path(__file__).resolve().parent
BENCHMARK = HERE / "benchmark.yaml"
REPORTS = HERE / "reports"
# Every 3rd case is held out: it is never inspected while improving the rules, so its
# score is the honest one. The rest is the development split.
def split_of(case_id: str) -> str:
    return "test" if int(case_id.lstrip("b")) % 3 == 0 else "dev"


CLASSES = ["correct", "incomplete", "misconception", "incorrect", "unclear", "guess", "blocked"]
NOT_UNDERSTOOD = {"incomplete", "misconception", "incorrect", "unclear", "guess"}


def _pct(n: int, d: int) -> float | None:
    return round(n / d, 4) if d else None


async def _predict(harness: PedagogicalHarness, case: dict) -> dict:
    cur = harness.curriculum
    topic, q = cur.question(case["question_id"])
    snap = StudentSnapshot(student_id="benchmark", mastery={c.id: 0.6 for _, c in cur.all_concepts()})
    res = await harness.run(topic, q, case["answer"], snap)
    # Baseline: answer-only grading, as a typical auto-marked quiz would do.
    parsed = parse_problem(GradingKey.from_question(q, []), topic.topic_id, case["answer"])
    baseline_credit = (not parsed.is_blank_or_guess) and matches(q.answer_patterns, parsed.normalized_answer)
    if isinstance(res, BlockedResult):
        return {
            "classification": "blocked",
            "safety": res.safety.category.value,
            "misconception_id": None,
            "answer_correct": None,
            "strategy": None,
            "baseline_credit": False,
            "first_reply": res.safety.student_message,
            "llm_steps": 0,
            "fallback_steps": 0,
        }
    v, d = res.verification, res.diagnosis
    return {
        "classification": v.classification,
        "safety": res.safety.category.value,
        "misconception_id": d.misconception_id,
        "answer_correct": v.answer_correct,
        "strategy": res.strategy.strategy.value,
        "mastery_after": res.mastery.after if res.mastery else None,
        "baseline_credit": baseline_credit,
        "first_reply": " ".join([*res.teaching.messages, res.teaching.follow_up or ""]),
        "llm_steps": sum(s.mode == "llm" for s in res.trace.steps),
        "fallback_steps": sum(s.mode == "fallback" for s in res.trace.steps),
    }


async def evaluate(mode: str = "rules", path: Path = BENCHMARK, llm: LLMClient | None = None, cases: list[dict] | None = None) -> dict:
    bench = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = bench["cases"] if cases is None else cases
    llm = llm or (DisabledLLMClient() if mode == "rules" else get_llm())
    harness = PedagogicalHarness(get_curriculum(), llm)

    rows = []
    for c in cases:
        p1 = await _predict(harness, c)
        p2 = await _predict(harness, c)
        g = c["expected"]
        rows.append(
            {
                "id": c["id"],
                "split": split_of(c["id"]),
                "question_id": c["question_id"],
                "category": c["category"],
                "answer": c["answer"],
                "gold": g,
                "pred": p1,
                "consistent": {k: p1[k] for k in ("classification", "misconception_id", "strategy")} == {k: p2[k] for k in ("classification", "misconception_id", "strategy")},
                "match": p1["classification"] == g["classification"],
            }
        )

    # --- classification
    confusion: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        confusion[r["gold"]["classification"]][r["pred"]["classification"]] += 1
    per_class = {}
    for k in CLASSES:
        tp = confusion[k][k]
        fn = sum(confusion[k].values()) - tp
        fp = sum(confusion[g][k] for g in CLASSES if g != k)
        prec, rec = _pct(tp, tp + fp), _pct(tp, tp + fn)
        f1 = round(2 * prec * rec / (prec + rec), 4) if prec and rec else 0.0
        per_class[k] = {"support": tp + fn, "precision": prec, "recall": rec, "f1": f1}

    # --- misconceptions
    gold_m = [r for r in rows if r["gold"].get("misconception_id")]
    pred_m = [r for r in rows if r["pred"]["misconception_id"]]
    m_recall = _pct(sum(r["pred"]["misconception_id"] == r["gold"]["misconception_id"] for r in gold_m), len(gold_m))
    m_precision = _pct(sum(r["pred"]["misconception_id"] == r["gold"].get("misconception_id") for r in pred_m), len(pred_m))

    # --- answer correctness
    ac = [r for r in rows if r["gold"].get("answer_correct") is not None and r["pred"]["answer_correct"] is not None]
    ac_agree = _pct(sum(r["gold"]["answer_correct"] == r["pred"]["answer_correct"] for r in ac), len(ac))

    # --- safety
    safety_by_cat = {}
    for cat in ("pii", "unsafe", "prompt_injection", "off_topic", "answer_request"):
        rs = [r for r in rows if r["gold"]["safety"] == cat]
        safety_by_cat[cat] = {"cases": len(rs), "caught": sum(r["pred"]["safety"] == cat for r in rs)}
    normal = [r for r in rows if r["gold"]["safety"] == "none"]
    false_alarms = sum(r["pred"]["safety"] != "none" for r in normal)
    flagged = sum(v["caught"] for v in safety_by_cat.values())
    total_safety = sum(v["cases"] for v in safety_by_cat.values())

    # --- understanding gate vs answer-only baseline
    gradable = [r for r in rows if r["gold"]["classification"] != "blocked"]
    not_understood = [r for r in gradable if r["gold"]["classification"] in NOT_UNDERSTOOD]
    understood = [r for r in gradable if r["gold"]["classification"] == "correct"]
    poor = [r for r in rows if r["category"] == "correct_poor_reasoning"]
    gate = {
        "not_understood_cases": len(not_understood),
        "understood_cases": len(understood),
        "curio_false_mastery_rate": _pct(sum(r["pred"]["classification"] == "correct" for r in not_understood), len(not_understood)),
        "baseline_false_mastery_rate": _pct(sum(r["pred"]["baseline_credit"] for r in not_understood), len(not_understood)),
        "curio_correct_credit_rate": _pct(sum(r["pred"]["classification"] == "correct" for r in understood), len(understood)),
        "baseline_correct_credit_rate": _pct(sum(r["pred"]["baseline_credit"] for r in understood), len(understood)),
        "poor_reasoning_cases": len(poor),
        "curio_false_mastery_on_poor_reasoning": _pct(sum(r["pred"]["classification"] == "correct" for r in poor), len(poor)),
        "baseline_false_mastery_on_poor_reasoning": _pct(sum(r["pred"]["baseline_credit"] for r in poor), len(poor)),
    }

    by_split = {}
    for sp in ("dev", "test"):
        rs = [r for r in rows if r["split"] == sp]
        nu = [r for r in rs if r["gold"]["classification"] in NOT_UNDERSTOOD]
        saf = [r for r in rs if r["gold"]["safety"] != "none"]
        by_split[sp] = {
            "cases": len(rs),
            "classification_accuracy": _pct(sum(r["match"] for r in rs), len(rs)),
            "safety_catch_rate": _pct(sum(r["pred"]["safety"] == r["gold"]["safety"] for r in saf), len(saf)),
            "curio_false_mastery_rate": _pct(sum(r["pred"]["classification"] == "correct" for r in nu), len(nu)),
            "baseline_false_mastery_rate": _pct(sum(r["pred"]["baseline_credit"] for r in nu), len(nu)),
        }

    by_category = {}
    for cat in sorted({r["category"] for r in rows}):
        rs = [r for r in rows if r["category"] == cat]
        by_category[cat] = {"cases": len(rs), "accuracy": _pct(sum(r["match"] for r in rs), len(rs))}

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "benchmark": {"path": str(path.relative_to(HERE.parent)), "version": bench.get("version"), "labeller": bench.get("labeller"), "cases": len(rows)},
        "metrics": {
            "classification_accuracy": _pct(sum(r["match"] for r in rows), len(rows)),
            "misconception_recall": m_recall,
            "misconception_precision": m_precision,
            "answer_correct_agreement": ac_agree,
            "safety_catch_rate": _pct(flagged, total_safety),
            "safety_false_alarm_rate": _pct(false_alarms, len(normal)),
            "decision_consistency": _pct(sum(r["consistent"] for r in rows), len(rows)),
        },
        "understanding_gate": gate,
        "by_split": by_split,
        "per_class": per_class,
        "confusion": {g: dict(confusion[g]) for g in CLASSES},
        "safety": safety_by_cat,
        "by_category": by_category,
        "cases": rows,
    }
    return report


def to_markdown(rep: dict) -> str:
    m, g = rep["metrics"], rep["understanding_gate"]
    f = lambda x: "—" if x is None else f"{x * 100:.1f}%"  # noqa: E731
    lines = [
        f"# Curio benchmark report ({rep['mode']} mode)",
        "",
        f"Generated {rep['generated_at']} · {rep['benchmark']['cases']} cases · labels: {rep['benchmark']['labeller']}",
        "",
        "## Headline metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        *[f"| {k.replace('_', ' ')} | {f(v)} |" for k, v in m.items()],
        "",
        "## Development vs held-out split",
        "",
        "This revision uses authored examples, independent regressions and **dev** errors; **test** case contents (every 3rd id) are not used to tune rules. "
        "Historical caveat: an earlier safety change was informed by one held-out case, so the safety catch rate is optimistic.",
        "",
        "| Split | Cases | Classification acc. | Safety catch | Curio false mastery | Baseline false mastery |",
        "|---|---|---|---|---|---|",
        *[
            f"| {k} | {v['cases']} | {f(v['classification_accuracy'])} | {f(v['safety_catch_rate'])} | {f(v['curio_false_mastery_rate'])} | {f(v['baseline_false_mastery_rate'])} |"
            for k, v in rep["by_split"].items()
        ],
        "",
        "## Understanding gate vs answer-only baseline",
        "",
        "| | Curio | Answer-only baseline |",
        "|---|---|---|",
        f"| False mastery on responses that do not show understanding (n={g['not_understood_cases']}) | {f(g['curio_false_mastery_rate'])} | {f(g['baseline_false_mastery_rate'])} |",
        f"| False mastery on correct-answer / poor-reasoning (n={g['poor_reasoning_cases']}) | {f(g['curio_false_mastery_on_poor_reasoning'])} | {f(g['baseline_false_mastery_on_poor_reasoning'])} |",
        f"| Credit given to fully correct responses (n={g['understood_cases']}) | {f(g['curio_correct_credit_rate'])} | {f(g['baseline_correct_credit_rate'])} |",
        "",
        "## Per-class",
        "",
        "| Class | Support | Precision | Recall | F1 |",
        "|---|---|---|---|---|",
        *[f"| {k} | {v['support']} | {f(v['precision'])} | {f(v['recall'])} | {f(v['f1'])} |" for k, v in rep["per_class"].items()],
        "",
        "## Misclassified cases",
        "",
        "| id | category | answer | gold | predicted |",
        "|---|---|---|---|---|",
        *[
            f"| {r['id']} | {r['category']} | {r['answer'][:70].replace('|', '/')} | {r['gold']['classification']} | {r['pred']['classification']} |"
            for r in rep["cases"]
            if not r["match"]
        ],
    ]
    return "\n".join(lines) + "\n"


def run_and_save(mode: str = "rules") -> dict:
    rep = asyncio.run(evaluate(mode))
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    (REPORTS / "latest.md").write_text(to_markdown(rep))
    return rep


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["rules", "llm"], default="rules")
    rep = run_and_save(ap.parse_args().mode)
    print(json.dumps({"metrics": rep["metrics"], "by_split": rep["by_split"]}, indent=1))
