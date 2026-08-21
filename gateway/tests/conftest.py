from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.core.config import get_settings
from app.gateway_pipeline import validation as validation_module
from app.routers import outcomes as outcomes_module


@dataclass
class _FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class _FakeMessage:
    content: list


class FakeMessages:
    """Stands in for anthropic.Anthropic().messages -- pops one scripted
    response per .create() call so tests can drive retry/fallback paths
    deterministically. Never makes a real API call."""

    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("FakeMessages: ran out of scripted responses")
        text = self._responses.pop(0)
        return _FakeMessage(content=[_FakeTextBlock(text=text)])


class FakeAnthropicClient:
    def __init__(self, responses: list[str]):
        self.messages = FakeMessages(responses)


@pytest.fixture
def env_setup(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("TENANT_API_KEYS", '{"quietnoise": "qn-test-key", "lorito": "lo-test-key"}')
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def fake_claude(monkeypatch, env_setup):
    """Call fake_claude(["<json response 1>", ...]) to script what the
    fake Claude client returns on each successive call within a test."""

    def _script(responses: list[str]) -> FakeAnthropicClient:
        fake_client = FakeAnthropicClient(responses)
        monkeypatch.setattr(validation_module, "get_client", lambda: fake_client)
        return fake_client

    return _script


@pytest.fixture
def fake_outcome_store(monkeypatch, env_setup):
    """Records calls instead of writing to real Firestore. Returns the
    list of recorded calls so tests can assert on what would have been
    written."""
    calls: list[dict] = []

    def _fake_write(tenant_id, module, mode, field_type, label):
        calls.append(
            {"tenant_id": tenant_id, "module": module, "mode": mode, "field_type": field_type, "label": label}
        )

    monkeypatch.setattr(outcomes_module, "write_outcome", _fake_write)
    return calls


@pytest.fixture
def client(env_setup):
    return TestClient(main_module.app)
