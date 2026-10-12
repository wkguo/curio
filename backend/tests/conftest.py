import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp()
os.environ["CURIO_DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["CURIO_HARNESS_MODE"] = "rules"

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def fresh_demo(client):
    client.post("/api/demo/reset")
    return client
