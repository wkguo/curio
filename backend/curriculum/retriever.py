"""Curriculum grounding: given a question, return the concept context the other
harness modules are allowed to use. Keeping retrieval explicit (rather than a
vector search) is deliberate for the MVP: the whole curriculum fits in memory and
the result is inspectable in the agent trace."""

from curriculum.loader import Curriculum
from schemas.curriculum import Question, Topic
from schemas.harness import CurriculumContext


def retrieve_context(curriculum: Curriculum, topic: Topic, question: Question) -> CurriculumContext:
    concept = topic.concept(question.concept)
    assert concept is not None  # guaranteed by Topic validation
    candidate = list(question.misconceptions)
    # Also consider misconceptions attached to the same concept elsewhere in the topic.
    for m in topic.misconceptions:
        if m.concept in {question.concept, *question.related_concepts} and m.id not in candidate:
            candidate.append(m.id)
    return CurriculumContext(
        topic_id=topic.topic_id,
        topic_name=topic.name,
        concept_id=concept.id,
        concept_name=concept.name,
        learning_objective=concept.learning_objective,
        key_ideas=concept.key_ideas,
        prerequisites=concept.prerequisites,
        related_concepts=question.related_concepts,
        candidate_misconceptions=candidate,
    )
