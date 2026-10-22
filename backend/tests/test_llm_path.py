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


class RecordingLLM(ScriptedLLM):
    def __init__(self):
        super().__init__()
        self.sent: list[str] = []

    async def generate(self, messages, schema=None):
        self.sent.extend(m["content"] for m in messages)
        return await super().generate(messages, schema)


@pytest.mark.asyncio
async def test_model_never_sees_student_identity_or_raw_personal_data():
    cur = get_curriculum()
    topic, q = cur.question("heat_001")
    llm = RecordingLLM()
    snap = StudentSnapshot(student_id="stu_7f3a", display_name="Xiaoming", mastery={"heat_conduction": 0.5, "heat_flow": 0.8})
    h = PedagogicalHarness(cur, llm)
    res = await h.run(topic, q, "Metal is colder than wood. call me 91234567 or xm.tan@gmail.com", snap)
    await h.run_transfer(topic, q, res.transfer, "the steel table, metal takes heat away faster. my ic is T1234567J", snap, None)
    sent = "\n".join(llm.sent)
    assert "[hidden]" in sent, "the model saw the answer, but only after redaction"
    for secret in ("stu_7f3a", "Xiaoming", "91234567", "xm.tan@gmail.com", "T1234567J"):
        assert secret not in sent


def test_extract_json_tolerates_fences_and_prose():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": 2} hope that helps') == {"a": 2}
    with pytest.raises(json.JSONDecodeError):
        extract_json("no json here")
