"""Loads and validates curriculum packs from curriculum/data/*.yaml."""

from functools import lru_cache
from pathlib import Path

import yaml

from schemas.curriculum import Question, Topic

DATA_DIR = Path(__file__).resolve().parent / "data"

# Display order in the UI. Unknown topics are appended alphabetically.
TOPIC_ORDER = ["heat_transfer", "forces", "matter"]


class CurriculumError(RuntimeError):
    pass


def load_topic_file(path: Path) -> Topic:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return Topic.model_validate(raw)
    except Exception as exc:
        raise CurriculumError(f"{path.name}: {exc}") from exc


class Curriculum:
    def __init__(self, topics: list[Topic]):
        order = {t: i for i, t in enumerate(TOPIC_ORDER)}
        self.topics = sorted(topics, key=lambda t: (order.get(t.topic_id, 99), t.topic_id))
        self._topics = {t.topic_id: t for t in self.topics}
        self._questions: dict[str, tuple[Topic, Question]] = {}
        self._concept_topic: dict[str, Topic] = {}
        for t in self.topics:
            for c in t.concepts:
                if c.id in self._concept_topic:
                    raise CurriculumError(f"duplicate concept id {c.id} in {t.topic_id}")
                self._concept_topic[c.id] = t
            for q in t.questions:
                if q.id in self._questions:
                    raise CurriculumError(f"duplicate question id {q.id} in {t.topic_id}")
                self._questions[q.id] = (t, q)

    def topic(self, topic_id: str) -> Topic | None:
        return self._topics.get(topic_id)

    def question(self, question_id: str) -> tuple[Topic, Question] | None:
        return self._questions.get(question_id)

    def topic_for_concept(self, concept_id: str) -> Topic | None:
        return self._concept_topic.get(concept_id)

    def all_concepts(self):
        for t in self.topics:
            for c in t.concepts:
                yield t, c


def load_curriculum(data_dir: Path = DATA_DIR) -> Curriculum:
    files = sorted(data_dir.glob("*.yaml"))
    if not files:
        raise CurriculumError(f"no curriculum packs found in {data_dir}")
    return Curriculum([load_topic_file(p) for p in files])


@lru_cache
def get_curriculum() -> Curriculum:
    return load_curriculum()
