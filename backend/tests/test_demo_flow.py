"""The scripted demo (spec §20/§21) is a contract: these numbers appear in the pitch."""


def test_scripted_demo_flow(fresh_demo):
    c = fresh_demo
    assert c.get("/api/students/demo_student/mastery").json()["concept_mastery"]["heat_conduction"] == 0.52
    s = c.post("/api/learning/sessions", json={"student_id": "demo_student", "topic_id": "heat_transfer"}).json()
    q = s["questions"][0]
    assert q["id"] == "heat_001"

    r = c.post("/api/learning/submit", json={"student_id": "demo_student", "question_id": "heat_001", "answer": q["demo_answers"]["misconception"]}).json()
    v = r["verification"]
    assert v["answer_correct"] is True and v["reasoning_correct"] is False
    assert r["diagnosis"]["misconception_id"] == "metal_is_colder"
    assert r["diagnosis"]["type"] == "CAUSAL_ERROR"
    assert r["teaching_strategy"] == "COUNTEREXAMPLE"
    assert (r["mastery_before"], r["mastery_after"]) == (0.52, 0.56)
    assert r["feedback"]["concerns"], "the flagged claim must be shown to the student"
    assert "expected_answer" not in r["transfer_question"], "grading key must never reach the client"
    assert [t["key"] for t in r["trace"]][:5] == ["safety", "curriculum", "parse", "reference", "verify"]
    assert r["learning_state"]["phase"] == "teaching"

    rep = c.post("/api/learning/reply", json={"student_id": "demo_student", "interaction_id": r["interaction_id"], "message": q["demo_answers"]["dialogue"]}).json()
    assert rep["resolved"] and rep["ready_for_transfer"]

    t = c.post("/api/learning/transfer", json={"student_id": "demo_student", "interaction_id": r["interaction_id"], "answer": r["transfer_demo_answer"]}).json()
    assert t["mastery_confirmed"] is True
    assert (t["mastery_before"], t["mastery_after"]) == (0.56, 0.76)

    trace = c.get(f"/api/analytics/traces/{r['trace_id']}").json()
    assert trace["final_mastery"] == 0.76 and trace["transfer_confirmed"] is True


def test_correct_answer_goes_straight_to_transfer(fresh_demo):
    c = fresh_demo
    r = c.post(
        "/api/learning/submit",
        json={"student_id": "demo_student", "question_id": "heat_001", "answer": "Both are at room temperature but metal is a good conductor so it takes heat away from my hand faster."},
    ).json()
    assert r["verification"]["reasoning_correct"] is True
    assert r["diagnosis"]["type"] is None
    assert r["teaching_strategy"] == "TRANSFER_EXAMPLE"
    assert r["teaching_response"]["ready_for_transfer"] is True
    assert r["mastery_after"] == round(0.52 + 0.2 * 0.5, 4)


def test_guess_is_not_evidence(fresh_demo):
    r = fresh_demo.post("/api/learning/submit", json={"student_id": "demo_student", "question_id": "heat_001", "answer": "I don't know"}).json()
    assert r["verification"]["is_guess"] is True
    assert r["diagnosis"]["type"] == "GUESS_WITHOUT_REASONING"
    assert r["mastery_after"] == r["mastery_before"]


def test_repeated_misconception_switches_strategy_and_lowers_mastery(fresh_demo):
    c = fresh_demo
    body = {"student_id": "demo_student", "question_id": "heat_001", "answer": "Metal is colder than wood."}
    first = c.post("/api/learning/submit", json=body).json()
    second = c.post("/api/learning/submit", json=body).json()
    assert second["diagnosis"]["is_repeated"] is True
    assert second["teaching_strategy"] != first["teaching_strategy"]
    assert second["mastery_after"] < second["mastery_before"]


def test_dialogue_is_bounded(fresh_demo):
    c = fresh_demo
    r = c.post("/api/learning/submit", json={"student_id": "demo_student", "question_id": "heat_001", "answer": "Metal is colder than wood."}).json()
    body = {"student_id": "demo_student", "interaction_id": r["interaction_id"], "message": "no idea"}
    one = c.post("/api/learning/reply", json=body).json()
    two = c.post("/api/learning/reply", json=body).json()
    assert not one["ready_for_transfer"]
    assert two["ready_for_transfer"], "after MAX_TURNS Curio states the key idea and moves on"


def test_misconception_text_never_earns_reasoning_credit(fresh_demo):
    """Regression: every question's misconception demo answer must not be praised for reasoning."""
    from curriculum.loader import get_curriculum

    for t in get_curriculum().topics:
        for q in t.questions:
            ans = q.demo_answers.misconception
            if not ans or not q.misconceptions:
                continue
            r = fresh_demo.post("/api/learning/submit", json={"student_id": "demo_student", "question_id": q.id, "answer": ans}).json()
            assert r["verification"]["misconceptions"], q.id
            assert not r["verification"]["reasoning_correct"], q.id
            praised = [s for s in r["feedback"]["strengths"] if s.startswith("You explained")]
            assert not praised, (q.id, praised)
