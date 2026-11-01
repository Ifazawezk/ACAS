"""The app starts and answers real requests. Importing it is what crashed on Python 3.12."""
import pytest


@pytest.fixture()
def client(anon, user_headers):
    anon.headers.update(user_headers)
    return anon


def test_health_is_ok(anon):
    assert anon.get("/health").json() == {"status": "ok", "db": "ok", "ai": "ok"}


def test_analyze_says_which_analyzer_ran(client):
    response = client.post("/ai/analyze", json={"content": "This API keeps crashing!"})
    assert response.status_code == 200
    assert response.json()["analyzer"] == "local"


def test_analyzed_comment_is_saved(client):
    text = "A comment that should reach the database"
    client.post("/ai/analyze", json={"content": text})
    assert text in [c["content"] for c in client.get("/comments/", params={"search": text}).json()]


def test_negative_comments_reach_the_dashboard_figure(client):
    # The dashboard used to count "angry" and "sad", but the analyzer says "anger" and "sadness".
    client.post("/ai/analyze", json={"content": "This is the worst service, I hate it"})
    assert client.get("/dashboard/metrics").json()["pct_negative"] > 0
