"""LLM-only baseline harness (evaluation/llm_only.py), driven by a scripted model."""

import re

import pytest

from evaluation.llm_only import check_health, compare, run_comparison, select_cases, to_markdown
from services.llm import LLMClient, LLMError


class OverTrustingLLM(LLMClient):
    """What a lenient tutor model does: credits everything and explains the answer."""

    @property
    def available(self):
        return True

    async def generate(self, messages, schema=None):
        if schema is None or schema.__name__ != "Verdict":
            raise LLMError("only the baseline prompt is scripted")
        key = re.search(r"Expected answer: (.*)", messages[-1]["content"]).group(1)
        return schema.model_validate({"classification": "correct", "understood": True, "reply": f"Great job! {key}"})


@pytest.mark.asyncio
async def test_baseline_report_measures_what_the_harness_prevents():
    rep = await compare(OverTrustingLLM(), with_curio_llm=True)
    llm, curio, curio_llm = (rep["systems"][k]["metrics"]["all"] for k in ("llm_only", "curio_rules", "curio_llm"))
    assert rep["systems"]["llm_only"]["calls"] == 2 * rep["cases"]  # every case run twice
    assert llm["false_mastery_rate"] == 1.0 and curio["false_mastery_rate"] < 0.2
    assert llm["raw_personal_data_sent_to_provider"] == 1.0
    assert curio["raw_personal_data_sent_to_provider"] is None  # no model call at all
    assert curio_llm["raw_personal_data_sent_to_provider"] == 0.0
    assert llm["gives_away_answer_when_asked"] > curio["gives_away_answer_when_asked"]
    assert "held-out test" in to_markdown(rep) and rep["systems"]["llm_only"]["metrics"]["test"]["n"] > 0


class FlakyLLM(OverTrustingLLM):
    """Fails, even after retries, on about a third of the prompts (bad JSON, refusals)."""

    async def generate(self, messages, schema=None):
        if len(messages[-1]["content"]) % 3 == 0:
            raise LLMError("bad json")
        return await super().generate(messages, schema)


@pytest.mark.asyncio
async def test_model_failures_are_excluded_from_rates_not_scored_as_wins(monkeypatch):
    import evaluation.llm_only as lo

    async def no_wait(_):
        return None

    monkeypatch.setattr(lo.asyncio, "sleep", no_wait)
    rep = await compare(FlakyLLM(), limit=30)
    m = rep["systems"]["llm_only"]["metrics"]["all"]
    assert m["errors"] > 0 and m["answered"] < 1.0
    assert m["false_mastery_rate"] == 1.0  # the failures did not dilute the rate
    with pytest.raises(SystemExit, match="ABORT"):
        check_health(rep)  # a third of the calls failed: no report is written


def test_limit_takes_evenly_spaced_cases_so_every_category_appears():
    import yaml

    from evaluation.run import BENCHMARK

    cases = select_cases(yaml.safe_load(BENCHMARK.read_text())["cases"], 30)
    assert len(cases) == 30 and {c["category"] for c in cases} >= {"safety", "misconception", "correct"}


@pytest.mark.asyncio
@pytest.mark.parametrize("fail_ping", [False, True])
async def test_cli_transport_stays_on_one_event_loop_and_always_closes(fail_ping):
    import asyncio

    class LoopBoundClient(OverTrustingLLM):
        def __init__(self):
            self.loop = None
            self.closed = False

        async def generate(self, messages, schema=None):
            loop = asyncio.get_running_loop()
            if self.loop is None:
                self.loop = loop
            assert loop is self.loop
            if schema.__name__ == "Ping":
                if fail_ping:
                    raise LLMError("offline")
                return schema(ok=True)
            return await super().generate(messages, schema)

        async def aclose(self):
            assert asyncio.get_running_loop() is self.loop
            self.closed = True

    client = LoopBoundClient()
    if fail_ping:
        with pytest.raises(SystemExit, match="ABORT"):
            await run_comparison(client, False, 2)
    else:
        report = await run_comparison(client, False, 2)
        assert report["cases"] == 2
    assert client.closed


@pytest.mark.asyncio
async def test_failed_repeat_judgements_cannot_slip_through_the_health_gate(monkeypatch):
    import evaluation.llm_only as lo

    async def no_wait(_):
        pass

    class RepeatFails(OverTrustingLLM):
        seen = set()

        async def generate(self, messages, schema=None):
            prompt = messages[-1]["content"]
            if prompt in self.seen:
                raise LLMError("repeat failed")
            self.seen.add(prompt)
            return await super().generate(messages, schema)

    monkeypatch.setattr(lo.asyncio, "sleep", no_wait)
    rep = await compare(RepeatFails(), limit=6)
    metrics = rep["systems"]["llm_only"]["metrics"]["all"]
    assert metrics["errors"] == 0
    assert metrics["repeat_errors"] == 6
    with pytest.raises(SystemExit, match="ABORT"):
        check_health(rep)
