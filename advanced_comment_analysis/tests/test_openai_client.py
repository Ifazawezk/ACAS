"""OpenAI mode, tested through the real SDK with only the HTTP layer replaced."""
import json

import httpx
import pytest
from openai import OpenAI

from app.services import ai_service, openai_client
from app.services.ai_service import analyze_text, parse_analysis
from app.services.openai_client import _openai_client, extract_comment_from_prompt

GOOD_ANSWER = {
    "emotion": "anger",
    "intent": "complaint",
    "priority": "High",
    "needs_ticket": True,
    "suggested_response": "We are sorry.",
    "confidence": 0.9,
}


def chat_reply(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 0,
            "model": "gpt-4o",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}],
        },
    )


@pytest.fixture()
def use_openai(monkeypatch):
    """Turn OpenAI mode on and answer every request with `handler`."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("FORCE_LOCAL", "false")
    monkeypatch.setattr(openai_client.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(ai_service.time, "sleep", lambda _seconds: None)

    def install(handler):
        transport = httpx.MockTransport(handler)
        client = OpenAI(api_key="sk-test", max_retries=0, http_client=httpx.Client(transport=transport))
        monkeypatch.setattr(openai_client, "_openai_client", lambda _key, _timeout: client)

    return install


def test_pinned_packages_can_build_the_client():
    # openai 1.34 cannot start with httpx 0.28 or newer, so the pin in requirements.txt matters.
    assert _openai_client("sk-test", 5) is not None


def test_answer_from_the_api_is_used(use_openai):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return chat_reply(json.dumps(GOOD_ANSWER))

    use_openai(handler)
    result = analyze_text("The app lost my order")

    assert result.analyzer == "openai"
    assert result.emotion == "anger"
    assert result.priority == "High"
    assert len(requests) == 1
    assert "The app lost my order" in requests[0]["messages"][0]["content"]


def test_answer_in_a_code_fence_is_parsed(use_openai):
    use_openai(lambda _request: chat_reply("```json\n" + json.dumps(GOOD_ANSWER) + "\n```"))
    assert analyze_text("Anything").analyzer == "openai"


def test_api_failure_falls_back_visibly(use_openai):
    calls = []

    def handler(_request):
        calls.append(1)
        return httpx.Response(500, json={"error": {"message": "server error"}})

    use_openai(handler)
    result = analyze_text("Anything")

    assert result.analyzer == "local"
    assert len(calls) == 3


def test_force_local_never_calls_the_api(use_openai, monkeypatch):
    def handler(_request):
        raise AssertionError("the API must not be called")

    use_openai(handler)
    monkeypatch.setenv("FORCE_LOCAL", "true")
    assert analyze_text("Anything").analyzer == "local"


def test_comment_containing_the_marker_is_kept_whole():
    prompt = ai_service.build_prompt("My COMMENT: this is broken")
    assert extract_comment_from_prompt(prompt) == "My COMMENT: this is broken"


def test_parse_analysis_keeps_an_analyzer_it_is_given():
    assert parse_analysis(json.dumps({**GOOD_ANSWER, "analyzer": "local"})).analyzer == "local"
