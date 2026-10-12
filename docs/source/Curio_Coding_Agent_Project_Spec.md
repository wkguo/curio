# Curio — AI Learning Verification & Teaching Agent

## 1. Project Goal

Curio is an AI-assisted learning platform for Singapore primary school students aged 10–12, starting with **Primary Science**.

The system should not behave like a normal chatbot that simply gives students answers.

Its core purpose is to determine whether a student **actually understands a scientific concept**, identify misconceptions in the student's reasoning, teach the missing concept, and then actively verify that the student can apply the concept again in a new situation.

The core pedagogical loop is:

```text
Verify → Validate → Teach → Question Back → Confirm Understanding
```

The MVP should be visually polished, interactive, easy to demo, and architected as a modular agent system.

---

# 2. Core Product Idea

A normal educational chatbot:

```text
Student Question
      ↓
     LLM
      ↓
   Answer
```

Curio:

```text
Student Response
      ↓
Curriculum Grounding
      ↓
Reasoning Verification
      ↓
Misconception Diagnosis
      ↓
Teaching Strategy Selection
      ↓
Personalized Teaching
      ↓
Transfer Question
      ↓
Mastery Verification
      ↓
Student Knowledge State Update
```

The system should optimize for:

```text
Understanding > Answer Accuracy
```

A correct final answer does **not** automatically imply mastery.

---

# 3. Recommended MVP Scope

Do not build the whole Singapore Primary Science curriculum initially.

Implement a polished demo around 3 science topics:

```text
1. Heat Transfer
2. Forces
3. Matter
```

Each topic should contain:

- 5–10 concepts
- 5–10 questions
- common misconceptions
- expected reasoning points
- follow-up questions
- mastery relationships

Example concept:

```yaml
concept_id: heat_conduction
topic: Heat Transfer
name: Heat Conduction
learning_objective:
  Explain that heat flows from a hotter region to a colder region.

prerequisites:
  - temperature
  - heat_energy

common_misconceptions:
  - Metal objects are naturally colder than plastic.
  - Metal creates coldness.
  - Objects at the same temperature always feel equally warm.

expected_reasoning:
  - Heat transfers from warmer to cooler regions.
  - Metals are generally better thermal conductors than plastic.
```

Static YAML/JSON files are completely acceptable for the MVP.

---

# 4. Main User Experience

## 4.1 Student Dashboard

The student should see:

- name/avatar
- current topic
- current mastery percentage
- concepts mastered
- concepts currently learning
- today's learning activity
- "Continue Learning" button

Example:

```text
Hi Alex 👋

Primary Science
Heat Transfer

Mastery: 68%

██████████████░░░░░░

✓ Temperature
✓ Heat Energy
◐ Heat Conduction
○ Insulators

Continue Learning
```

---

## 4.2 Learning Session

Main learning interface:

```text
┌──────────────────────────────────────┐
│ Heat Transfer                       │
│ Question 3 / 5                      │
├──────────────────────────────────────┤
│                                      │
│ Why does a metal spoon feel colder  │
│ than a wooden spoon in the same     │
│ room?                               │
│                                      │
│ [Student answer input]              │
│                                      │
│              Submit Answer          │
└──────────────────────────────────────┘
```

After submission, do not immediately reveal a full answer.

Display an analysis panel.

Example:

```text
Curio is checking your reasoning...

✓ You noticed that metal and wood behave differently.

⚠ But one idea needs another look:

"Metal is naturally colder."

Both objects may actually have the same temperature.

Let's investigate why they feel different.
```

Then proceed into a short teaching interaction.

---

# 5. Pedagogical Agent Harness

Implement the learning pipeline as modular components.

Recommended modules:

```text
Problem Parser
Curriculum Retriever
Reference Solver
Reasoning Verifier
Misconception Classifier
Teaching Policy
Teaching Agent
Transfer Question Generator
Question Quality Verifier
Mastery Estimator
```

Do NOT create 10 independent autonomous agents.

They can simply be Python services/functions connected through one orchestrator.

Recommended implementation:

```python
class PedagogicalHarness:

    async def run(self, question, student_answer, student_state):

        curriculum = await curriculum_retriever(question)

        reference = await reference_solver(
            question,
            curriculum
        )

        verification = await reasoning_verifier(
            question,
            student_answer,
            reference,
            curriculum
        )

        diagnosis = await misconception_classifier(
            verification,
            curriculum
        )

        strategy = teaching_policy(
            diagnosis,
            student_state
        )

        teaching_response = await teaching_agent(
            strategy,
            diagnosis,
            curriculum
        )

        transfer_question = await question_generator(
            diagnosis,
            curriculum
        )

        return {
            "verification": verification,
            "diagnosis": diagnosis,
            "strategy": strategy,
            "teaching_response": teaching_response,
            "transfer_question": transfer_question
        }
```

---

# 6. Structured Reasoning Verification

The verifier should return structured JSON rather than free-form text.

Example schema:

```json
{
  "answer_correct": true,
  "reasoning_correct": false,
  "confidence": 0.91,
  "concepts_detected": [
    "temperature",
    "thermal_conduction"
  ],
  "missing_concepts": [
    "heat_transfer_rate"
  ],
  "misconceptions": [
    {
      "type": "causal_error",
      "statement": "metal is naturally colder",
      "concept": "thermal_conduction",
      "severity": "medium"
    }
  ],
  "reasoning_summary": "The student correctly noticed the material difference but incorrectly attributes the sensation to metal having a lower temperature."
}
```

Use Pydantic schemas to enforce structured output.

---

# 7. Misconception Categories

Keep the classification simple.

```text
FACTUAL_ERROR
CAUSAL_ERROR
CONCEPT_CONFUSION
MISSING_STEP
OVERGENERALIZATION
VOCABULARY_CONFUSION
CORRECT_BUT_INCOMPLETE
GUESS_WITHOUT_REASONING
```

Example:

```json
{
  "type": "CONCEPT_CONFUSION",
  "concept": "thermal_conduction",
  "student_claim": "metal is colder",
  "corrective_target": "thermal conductivity affects heat transfer rate"
}
```

---

# 8. Teaching Policy

The system should choose a teaching action based on the diagnosis.

Supported actions:

```text
DIRECT_HINT
SOCRATIC_QUESTION
ANALOGY
COUNTEREXAMPLE
SIMPLER_EXPLANATION
PREREQUISITE_REVIEW
VISUAL_EXPLANATION
TRANSFER_EXAMPLE
```

Simple heuristic policy is enough for MVP.

Example:

```python
def select_strategy(diagnosis):

    if diagnosis.type == "FACTUAL_ERROR":
        return "DIRECT_HINT"

    if diagnosis.type == "CAUSAL_ERROR":
        return "COUNTEREXAMPLE"

    if diagnosis.type == "CONCEPT_CONFUSION":
        return "ANALOGY"

    if diagnosis.type == "MISSING_STEP":
        return "SOCRATIC_QUESTION"

    return "SIMPLER_EXPLANATION"
```

Future versions can learn this policy from student interaction data.

---

# 9. Question Back / Transfer Verification

This is a core Curio feature.

After teaching, generate a new question that tests the **same scientific concept in a different surface context**.

Original:

```text
Why does a metal spoon feel colder than a wooden spoon?
```

Transfer question:

```text
Two cups contain cold water.

One cup is metal and the other is plastic.

Which cup will transfer heat from your hand faster, and why?
```

The student must answer again.

The follow-up question should:

- test the same concept
- use a different example
- not simply repeat the original question
- stay within the target age level
- have a clear expected answer
- avoid introducing unnecessary new concepts

---

# 10. Question Quality Verifier

Before showing an AI-generated transfer question, run a lightweight validation step.

Return:

```json
{
  "same_concept": true,
  "age_appropriate": true,
  "answerable": true,
  "curriculum_aligned": true,
  "difficulty": "similar",
  "approved": true
}
```

If rejected, regenerate once.

Do not create infinite agent loops.

---

# 11. Student Knowledge Model

Each student has a lightweight mastery state.

Example:

```json
{
  "student_id": "demo_student",
  "concept_mastery": {
    "temperature": 0.91,
    "heat_energy": 0.82,
    "thermal_conduction": 0.52,
    "insulation": 0.35
  }
}
```

After each interaction:

```text
Correct answer + correct reasoning
→ strong mastery increase

Correct answer + incorrect reasoning
→ small/no mastery increase

Incorrect answer + good partial reasoning
→ small mastery increase

Transfer question success
→ strong mastery confirmation
```

Simple update rule:

```python
mastery_new = mastery_old + learning_rate * evidence
```

Example evidence:

```text
1.0   correct reasoning + transfer success
0.5   correct reasoning
0.2   partial understanding
0.0   guess
-0.1  repeated misconception
```

Clamp mastery into:

```text
0.0 – 1.0
```

No complex Bayesian model is necessary for MVP.

---

# 12. Mastery Visualization

Make mastery visually appealing.

Example:

```text
Heat Transfer

Temperature          ████████████████  91%
Heat Energy          ██████████████    82%
Heat Conduction      █████████         52%
Insulation           ██████            35%
```

Also provide a concept graph.

Example:

```text
Temperature
    │
    ▼
Heat Energy
    │
    ▼
Heat Transfer
   / \
  /   \
Conduction   Insulation
```

Recommended frontend library:

```text
React Flow
```

Nodes should visually represent mastery:

```text
Mastered
Learning
Needs Practice
Locked
```

---

# 13. Teacher / Demo Dashboard

A second dashboard makes the system much more impressive.

Display:

```text
Class Understanding Overview

Students: 24
Questions answered: 186
Verified mastery rate: 72%

Top misconceptions

1. Heat vs Temperature        14 students
2. Force vs Motion             9 students
3. Melting vs Dissolving       7 students
```

Also show:

```text
AI Diagnosis Trace
```

Example:

```text
Student Answer
      ↓
Answer Correct: YES
      ↓
Reasoning Correct: NO
      ↓
Misconception:
Metal is inherently colder
      ↓
Teaching Strategy:
Counterexample
      ↓
Transfer Question
      ↓
Mastery:
0.52 → 0.76
```

This trace should be one of the strongest visual demo components.

---

# 14. Recommended UI Style

The UI should feel:

```text
friendly
clean
modern
educational
not childish
not enterprise-like
```

Reference visual direction:

```text
Duolingo × Khan Academy × modern AI copilot
```

Suggested layout:

```text
Left Sidebar
    Dashboard
    Learn
    Progress
    Concepts

Main Area
    Learning interaction

Right Panel
    Concept mastery
    Curio insight
```

Use subtle animation for:

```text
reasoning verification
mastery updates
concept graph state
agent processing steps
```

Example processing animation:

```text
Curio is thinking...

✓ Checking your answer
✓ Comparing reasoning
✓ Finding the concept
● Looking for misconceptions
○ Preparing a follow-up
```

---

# 15. Recommended Frontend Stack

Use:

```text
Next.js
TypeScript
Tailwind CSS
shadcn/ui
Framer Motion
React Flow
Recharts
Lucide Icons
```

Recommended project:

```text
frontend/
```

Pages:

```text
/
    Landing / Demo

/dashboard
    Student dashboard

/learn
    Interactive learning session

/progress
    Concept mastery visualization

/teacher
    Teacher analytics dashboard
```

---

# 16. Recommended Backend Stack

Use:

```text
Python 3.11+
FastAPI
Pydantic
SQLAlchemy
SQLite for MVP
```

AI:

```text
OpenAI-compatible LLM API
```

Keep model provider abstract:

```python
class LLMClient:
    async def generate(self, messages, schema=None):
        ...
```

This allows switching between OpenAI, Gemini, Claude, Qwen, etc.

---

# 17. Backend Structure

Recommended repository:

```text
curio/
│
├── frontend/
│
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── types/
│
├── backend/
│
│   ├── main.py
│   │
│   ├── api/
│   │   ├── learning.py
│   │   ├── students.py
│   │   └── analytics.py
│   │
│   ├── harness/
│   │   ├── orchestrator.py
│   │   ├── verifier.py
│   │   ├── misconception.py
│   │   ├── teaching_policy.py
│   │   ├── teaching_agent.py
│   │   ├── question_generator.py
│   │   └── mastery.py
│   │
│   ├── curriculum/
│   │   ├── loader.py
│   │   ├── retriever.py
│   │   └── data/
│   │       ├── heat_transfer.yaml
│   │       ├── forces.yaml
│   │       └── matter.yaml
│   │
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── database/
│
└── README.md
```

---

# 18. Important API Endpoints

## Submit Answer

```http
POST /api/learning/submit
```

Request:

```json
{
  "student_id": "demo_student",
  "question_id": "heat_001",
  "answer": "Metal is colder because metal naturally has a lower temperature."
}
```

Response:

```json
{
  "verification": {},
  "diagnosis": {},
  "teaching_strategy": "COUNTEREXAMPLE",
  "teaching_response": "...",
  "transfer_question": {},
  "mastery_before": 0.52,
  "mastery_after": 0.56
}
```

---

## Submit Transfer Answer

```http
POST /api/learning/transfer
```

Response:

```json
{
  "mastery_confirmed": true,
  "mastery_before": 0.56,
  "mastery_after": 0.76,
  "feedback": "Great — this time your explanation correctly uses heat transfer."
}
```

---

## Student State

```http
GET /api/students/{student_id}/mastery
```

---

## Teacher Analytics

```http
GET /api/analytics/class
```

---

# 19. LLM Prompt Architecture

Avoid giant prompts.

Use separate prompts.

Recommended:

```text
prompts/
    reference_solver.txt
    reasoning_verifier.txt
    misconception_classifier.txt
    teaching_agent.txt
    question_generator.txt
    question_verifier.txt
```

Each prompt should include:

```text
ROLE
TASK
CURRICULUM CONTEXT
STUDENT AGE
INPUT
OUTPUT SCHEMA
CONSTRAINTS
```

Important constraint:

```text
Never reveal the full solution immediately if the student can still reason toward it.
```

---

# 20. Example Learning Session

Question:

```text
A metal spoon and a wooden spoon have been in the same room overnight.

Why does the metal spoon feel colder?
```

Student:

```text
Because metal is colder than wood.
```

Verifier:

```text
Answer quality: partially correct

Misconception:
The student believes metal has a lower temperature.
```

Curio:

```text
Interesting idea.

But imagine both spoons have been in the same room all night.

Would they eventually reach roughly the same room temperature?

What might be different about how metal and wood interact with heat from your hand?
```

Student:

```text
Maybe metal takes heat from my hand faster.
```

Curio:

```text
Exactly.

Metal transfers heat away from your hand faster than wood.

That faster heat transfer makes the metal feel colder, even when both objects are at the same temperature.
```

Transfer question:

```text
A metal chair and a plastic chair have been kept in the same air-conditioned room.

Which one is likely to feel colder when you first touch it, and why?
```

Student:

```text
The metal chair because it transfers heat away from my body faster.
```

Result:

```text
Concept mastery confirmed

Thermal Conduction

52% → 78%
```

---

# 21. Demo Mode

Add a predefined demo student:

```text
Alex
Primary 5
```

Allow one-click reset.

Demo sequence should be deterministic enough to reliably show:

```text
correct answer
+
incorrect reasoning
+
misconception detection
+
teaching intervention
+
transfer question
+
mastery improvement
```

This is more impressive than a generic chatbot demo.

---

# 22. Agent Trace Visualization

Store each harness step:

```json
[
  {
    "step": "Curriculum Retrieval",
    "status": "complete",
    "duration_ms": 120
  },
  {
    "step": "Reasoning Verification",
    "status": "complete",
    "duration_ms": 850
  },
  {
    "step": "Misconception Diagnosis",
    "status": "complete",
    "duration_ms": 420
  },
  {
    "step": "Teaching Strategy",
    "status": "complete",
    "duration_ms": 20
  }
]
```

Render it as a visual pipeline.

Example:

```text
Curriculum
    ↓
Reasoning
    ↓
Diagnosis
    ↓
Teaching
    ↓
Transfer
    ↓
Mastery
```

The UI should allow the teacher/demo user to inspect individual steps.

---

# 23. Database Tables

Minimal tables:

```text
students
questions
concepts
student_mastery
learning_sessions
student_responses
agent_traces
```

Example:

```text
student_mastery

student_id
concept_id
mastery_score
attempt_count
last_updated
```

---

# 24. Safety / Product Constraints

Because this is designed for children:

- avoid collecting unnecessary personal data
- do not expose raw model prompts
- do not provide unrestricted general chatbot functionality
- stay within curriculum context
- avoid asking sensitive personal questions
- keep explanations age appropriate
- log AI-generated educational content
- provide deterministic fallback messages if model calls fail

For MVP, no authentication is required.

Use demo users.

---

# 25. Error Handling

If LLM call fails:

```text
"Curio is having trouble checking that answer right now.
Let's try this question another way."
```

Do not expose:

```text
API error
stack trace
JSON parse error
```

If structured output fails:

1. retry once
2. use fallback parser
3. return safe generic teaching response

---

# 26. MVP Priorities

## P0 — Must Work

```text
Student learning page
Question answering
Reasoning verification
Misconception diagnosis
Teaching response
Transfer question
Mastery update
Student progress dashboard
```

## P1 — Strong Demo Value

```text
Teacher dashboard
Concept graph
Agent trace visualization
Animated reasoning steps
Misconception analytics
```

## P2 — Optional

```text
Voice interaction
Image questions
OCR
Full curriculum ingestion
Real teacher accounts
RL teaching policy
```

Do NOT implement P2 before P0/P1 are polished.

---

# 27. Development Strategy

Recommended order:

```text
Phase 1
Static frontend + mocked responses

Phase 2
Curriculum YAML + backend schemas

Phase 3
Reasoning verifier

Phase 4
Misconception + teaching pipeline

Phase 5
Transfer-question loop

Phase 6
Mastery tracking

Phase 7
Teacher dashboard + visualization

Phase 8
Polish / animations / demo data
```

Important:

Build the full UI using mocked backend responses first.

The project should already look impressive before integrating the real LLM pipeline.

---

# 28. Acceptance Criteria

The MVP is complete when a user can:

1. Open the Curio dashboard.
2. Select Heat Transfer.
3. Answer a science question.
4. See Curio analyze both answer and reasoning.
5. See a misconception identified.
6. Receive an age-appropriate teaching intervention.
7. Answer a new transfer question.
8. Have mastery updated.
9. See the concept mastery visualization.
10. Open the teacher dashboard and inspect the complete learning trace.

---

# 29. Product Message

The main message should remain:

> Curio does not simply check whether students get the right answer.  
> It verifies whether they understand why the answer is right.

Short tagline options:

```text
Don't just answer. Understand.

AI that verifies learning.

From correct answers to real understanding.
```

---

# 30. Instructions for Coding Agent

Implement this as a polished MVP rather than a research prototype.

Priorities:

```text
1. Reliable end-to-end learning flow
2. Strong visual design
3. Clear modular architecture
4. Structured LLM outputs
5. Easy demo experience
```

Do not over-engineer:

- authentication
- distributed systems
- vector databases
- complex multi-agent frameworks
- reinforcement learning
- production cloud infrastructure

Simple implementations are preferred where possible.

However, keep the modules sufficiently separated so that more advanced student modeling, multimodal interaction, and learned teaching policies can be added later.

The final product should feel like a real education technology product, not an LLM API demo.
