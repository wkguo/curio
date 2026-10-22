"""Export API responses as frontend fixtures for offline demo mode.

The frontend falls back to these when the backend is unreachable, so the UI can be
demoed (or deployed statically) with zero setup. Fixtures are produced by the real
backend, so they cannot drift from the API contract.

    uv run python scripts/export_fixtures.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
tmp = tempfile.mkdtemp()
os.environ["CURIO_DATABASE_URL"] = f"sqlite:///{tmp}/fixtures.db"
os.environ["CURIO_HARNESS_MODE"] = "rules"

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "frontend" / "public" / "mock" / "fixtures.json"
SID = "demo_student"


def main() -> None:
    fx: dict = {"flows": {}}
    with TestClient(app) as c:
        get = lambda url: c.get(url).json()  # noqa: E731
        fx["health"] = {**get("/api/health"), "offline": True}
        fx["students"] = get("/api/students")
        fx["topics"] = get(f"/api/curriculum/topics?student_id={SID}")
        fx["topic_details"] = {t["topic_id"]: get(f"/api/curriculum/topics/{t['topic_id']}?student_id={SID}") for t in fx["topics"]}
        fx["mastery"] = get(f"/api/students/{SID}/mastery")
        fx["dashboard"] = get(f"/api/students/{SID}/dashboard")
        fx["sessions"] = {
            t["topic_id"]: c.post("/api/learning/sessions", json={"student_id": SID, "topic_id": t["topic_id"], "size": 10}).json() for t in fx["topics"]
        }
        fx["analytics"] = get("/api/analytics/class")
        fx["traces"] = get("/api/analytics/traces?limit=30")
        fx["trace_details"] = {t["id"]: get(f"/api/analytics/traces/{t['id']}") for t in fx["traces"][:30]}
        fx["queue"] = get("/api/teacher/queue")
        fx["pathways"] = get("/api/teacher/pathways")
        fx["privacy"] = get(f"/api/privacy/students/{SID}")
        fx["evaluation"] = c.post("/api/evaluation/run?mode=rules").json()
        fx["llm_comparison"] = get("/api/evaluation/llm-baseline")

        # One scripted flow per question: misconception → dialogue → transfer.
        for topic_id, sess in fx["sessions"].items():
            for q in sess["questions"]:
                demo = q.get("demo_answers", {})
                ans = demo.get("misconception") or demo.get("correct") or "I think it is because of heat."
                sub = c.post("/api/learning/submit", json={"student_id": SID, "question_id": q["id"], "answer": ans}).json()
                rep = c.post(
                    "/api/learning/reply", json={"student_id": SID, "interaction_id": sub["interaction_id"], "message": demo.get("dialogue") or "ok"}
                ).json()
                tr = c.post(
                    "/api/learning/transfer",
                    json={"student_id": SID, "interaction_id": sub["interaction_id"], "answer": sub.get("transfer_demo_answer") or "because of heat"},
                ).json()
                fx["flows"][q["id"]] = {"submit": sub, "reply": rep, "transfer": tr}
                c.post("/api/demo/reset")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fx, ensure_ascii=False, default=str))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB, {len(fx['flows'])} flows)")


if __name__ == "__main__":
    main()
