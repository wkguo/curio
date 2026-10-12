import subprocess
import sys
from pathlib import Path

from curriculum.loader import load_curriculum


def test_all_packs_load_and_cross_reference():
    cur = load_curriculum()
    assert [t.topic_id for t in cur.topics] == ["heat_transfer", "forces", "matter"]
    for t in cur.topics:
        assert 5 <= len(t.concepts) <= 10
        assert 5 <= len(t.questions) <= 10
        assert t.misconceptions


def test_curriculum_linter_passes():
    script = Path(__file__).resolve().parent.parent / "scripts" / "check_curriculum.py"
    out = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
