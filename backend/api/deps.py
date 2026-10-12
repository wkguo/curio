from curriculum.loader import Curriculum, get_curriculum
from harness.orchestrator import PedagogicalHarness
from services.llm import get_llm


def curriculum_dep() -> Curriculum:
    return get_curriculum()


def harness_dep() -> PedagogicalHarness:
    return PedagogicalHarness(get_curriculum(), get_llm())
