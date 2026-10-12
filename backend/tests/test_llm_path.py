"""LLM path: structured output, retry-once, reconciliation and fallback (spec §6, §25)."""

import json

import pytest

from curriculum.loader import get_curriculum
from harness.context import StudentSnapshot
from harness.orchestrator import PedagogicalHarness
from services.llm import LLMClient, LLMError, extract_json


class ScriptedLLM(LLMClient):
    name = "scripted"

    def __init__(self, fail=False):
        self.fail, self.calls = fail, []

    @property
    def available(self):
        return True

    async def generate(self, messages, schema=None):
        self.calls.append(schema.__name__ if schema else "text")
        if self.fail:
            raise LLMError("down")
        if schema.__name__ == "Verification":
            # The model misses the curated misconception; reconciliation must add it back.
            return schema.model_validate(
                {"answer_correct": True, "reasoning_correct": True, "confidence": 0.8, "quality": "correct", "reasoning_summary": "ok", "reasoning_points_hit": ["bogus_id"]}
            )
        if schema.__name__ == "GeneratedQuestion":
            return schema.model_validate(
                {
                    "id": "x",
                    "concept": "heat_conduction",
                    "prompt": "At the hawker centre, a steel table and a plastic stool are in the shade. Which feels colder to touch, and why?",
                    "emoji": "chair",
                    "expected_answer": "The steel table, because metal conducts heat away from your hand faster.",
                    "expected_reasoning": ["Metal conducts heat away faster."],
                }
            )
        if schema.__name__ == "QuestionQuality":
            return schema.model_validate({"same_concept": True, "age_appropriate": True, "answerable": True, "curriculum_aligned": True, "difficulty": "similar", "approved": True})
        raise LLMError("unexpected schema")


def _snapshot():
    return StudentSnapshot(student_id="t", mastery={"heat_conduction": 0.5, "heat_flow": 0.8})


@pytest.mark.asyncio
async def test_llm_verification_is_reconciled_with_curated_misconceptions():
    cur = get_curriculum()
    topic, q = cur.question("heat_001")
    llm = ScriptedLLM()
    res = await PedagogicalHarness(cur, llm).run(topic, q, "Metal is colder than wood.", _snapshot())
    assert res.verification.reasoning_correct is False
    assert "metal_is_colder" in [m.id for m in res.verification.misconceptions]
    assert res.verification.reasoning_points_hit == []  # invalid ids dropped
    assert res.transfer.source == "generated"
    assert {s.mode for s in res.trace.steps} >= {"llm"}


@pytest.mark.asyncio
async def test_llm_outage_falls_back_to_rules_without_error():
    cur = get_curriculum()
    topic, q = cur.question("heat_001")
    res = await PedagogicalHarness(cur, ScriptedLLM(fail=True)).run(topic, q, "Metal is colder than wood.", _snapshot())
    assert res.diagnosis.misconception_id == "metal_is_colder"
    assert res.transfer.source == "authored"
    assert any(s.status == "fallback" for s in res.trace.steps)


def test_extract_json_tolerates_fences_and_prose():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": 2} hope that helps') == {"a": 2}
    with pytest.raises(json.JSONDecodeError):
        extract_json("no json here")
