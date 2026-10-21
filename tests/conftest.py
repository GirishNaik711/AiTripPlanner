import httpx
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

import main

TOKEN = "test-token-0123456789abcdef"
SESSION = "5f0b7a9e-2d0f-4c1e-9a53-7c1d2f6a8b11"


class StubAgent:
    def __init__(self, reply="Pack light. Try not to lose your passport.", errors=None):
        self.reply = reply
        self.errors = list(errors or [])
        self.calls = []

    def invoke(self, payload, config=None):
        self.calls.append((payload["messages"], config))
        if self.errors:
            raise self.errors.pop(0)
        return {"messages": [AIMessage(content=self.reply)]}


class StubGate:
    def __init__(self, verdict="Yes", error=None):
        self.verdict = verdict
        self.error = error
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        if self.error:
            raise self.error
        return AIMessage(content=self.verdict)


def groq_bad_request():
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    import groq
    return groq.BadRequestError("tool_use_failed", response=httpx.Response(400, request=request), body=None)


@pytest.fixture
def agent():
    return StubAgent()


@pytest.fixture
def gate():
    return StubGate()


@pytest.fixture
def client(monkeypatch, agent, gate):
    monkeypatch.setenv("API_AUTH_TOKEN", TOKEN)
    monkeypatch.setattr(main, "build_agent", lambda: agent)
    monkeypatch.setattr(main, "build_gate", lambda: gate)
    main.sessions.clear()
    main.limiter.reset()
    with TestClient(main.app) as test_client:
        yield test_client
    main.limiter.reset()


def ask(client, question="Plan 3 days in Lisbon on a budget", session_id=SESSION, token=TOKEN):
    headers = {"X-API-Key": token} if token is not None else {}
    return client.post("/query", json={"question": question, "session_id": session_id}, headers=headers)
