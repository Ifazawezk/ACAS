"""The app starts and answers real requests. Importing it is what crashed on Python 3.12."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from app.main import app

    # The context manager runs the startup hook, which creates the tables.
    with TestClient(app) as test_client:
        yield test_client


def test_health_is_ok(client):
    assert client.get("/health").json() == {"status": "ok", "db": "ok", "ai": "ok"}


def test_analyze_says_which_analyzer_ran(client):
    response = client.post("/ai/analyze", json={"content": "This API keeps crashing!"})
    assert response.status_code == 200
    assert response.json()["analyzer"] == "local"


def test_analyzed_comment_is_saved(client):
    text = "A comment that should reach the database"
    client.post("/ai/analyze", json={"content": text})
    assert text in [c["content"] for c in client.get("/comments/", params={"search": text}).json()]
