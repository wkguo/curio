"""Renders the per-step prompt templates in backend/prompts/ (spec §19).

Templates use `$name` placeholders (string.Template) so JSON braces need no escaping.
Prompts are server-side only and are never returned to the client or stored in traces.
"""

from functools import lru_cache
from pathlib import Path
from string import Template

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache
def _template(name: str) -> Template:
    return Template((PROMPT_DIR / f"{name}.txt").read_text(encoding="utf-8"))


def render(name: str, *, student_age: int = 11, level: str = "Primary 5", **values) -> str:
    constraints = _template("_shared_constraints").safe_substitute(student_age=student_age, level=level)
    return _template(name).safe_substitute(student_age=student_age, level=level, constraints=constraints, **values)


def bullet(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) or "- (none)"


def system_user(prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "You are part of Curio, a safe science-learning app for children aged 10–12."},
        {"role": "user", "content": prompt},
    ]
