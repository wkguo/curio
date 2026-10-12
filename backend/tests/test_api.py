from harness.orchestrator import PedagogicalHarness


def test_read_endpoints(client):
    for url in [
        "/api/health",
        "/api/students",
        "/api/students/demo_student/dashboard",
        "/api/curriculum/topics?student_id=demo_student",
        "/api/curriculum/topics/forces?student_id=demo_student",
        "/api/analytics/class",
        "/api/analytics/traces",
    ]:
        assert client.get(url).status_code == 200, url


def test_class_analytics_shape(client):
    a = client.get("/api/analytics/class").json()
    assert a["students"] == 24
    assert a["top_misconceptions"]
    assert 0 <= a["verified_mastery_rate"] <= 1


def test_unknown_ids_are_404(client):
    assert client.get("/api/students/nobody/mastery").status_code == 404
    assert client.post("/api/learning/submit", json={"student_id": "demo_student", "question_id": "nope", "answer": "hi there"}).status_code == 404


def test_harness_crash_returns_safe_message(client, monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("secret stack detail")

    monkeypatch.setattr(PedagogicalHarness, "run", boom)
    r = client.post("/api/learning/submit", json={"student_id": "demo_student", "question_id": "heat_001", "answer": "metal is colder"})
    assert r.status_code == 503
    body = r.json()
    assert body["code"] == "curio_unavailable"
    assert "secret" not in r.text and "Traceback" not in r.text
