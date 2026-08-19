import json

from app.gateway_pipeline.validation import generate_completion
from app.modules.visionary import VisionaryModule
from app.schemas.context import CompletionRequest

VALID_RESPONSE = json.dumps(
    {
        "missing_variables": [],
        "strategic_critique": "Solid, ship it.",
        "generated_content": "We believe downtime should be extinct.",
        "suggested_next_action": None,
        "sourced_fields": {},
    }
)

UNGROUNDED_RESPONSE = json.dumps(
    {
        "missing_variables": [],
        "strategic_critique": "Solid, ship it.",
        "generated_content": "Chevron's $850k deal closes Friday.",
        "suggested_next_action": None,
        "sourced_fields": {"deal value": "deal_value"},  # not in context
    }
)

NOT_JSON_RESPONSE = "Sure, here's a great positioning statement for you!"


def _request(**overrides) -> CompletionRequest:
    defaults = dict(
        tenant_id="quietnoise",
        module="visionary",
        mode=None,
        user_message="Position our new product.",
        context={"enemy": "legacy SCADA vendors"},
    )
    defaults.update(overrides)
    return CompletionRequest(**defaults)


def test_first_attempt_success(fake_claude):
    fake_claude([VALID_RESPONSE])
    result = generate_completion(VisionaryModule(), _request())
    assert result.resolved_via == "first_attempt"
    assert result.generated_content


def test_invisible_retry_on_bad_json_then_succeeds(fake_claude):
    fake_claude([NOT_JSON_RESPONSE, VALID_RESPONSE])
    result = generate_completion(VisionaryModule(), _request())
    assert result.resolved_via == "invisible_retry"
    assert result.generated_content


def test_grounding_check_rejects_unsourced_claim_then_recovers(fake_claude):
    fake_claude([UNGROUNDED_RESPONSE, VALID_RESPONSE])
    result = generate_completion(VisionaryModule(), _request())
    assert result.resolved_via == "invisible_retry"


def test_graceful_fallback_when_no_model_backend_configured(monkeypatch, env_setup):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        result = generate_completion(VisionaryModule(), _request())
        assert result.resolved_via == "graceful_fallback"
        assert result.generated_content == ""
        assert "no model backend configured" in result.strategic_critique.lower()
    finally:
        get_settings.cache_clear()


def test_graceful_fallback_after_exhausting_retries(fake_claude):
    # max_invisible_retries defaults to 2 -> 3 total attempts allowed.
    fake_claude([NOT_JSON_RESPONSE, NOT_JSON_RESPONSE, NOT_JSON_RESPONSE])
    result = generate_completion(VisionaryModule(), _request())
    assert result.resolved_via == "graceful_fallback"
    assert result.generated_content == ""
    assert "core belief" in result.strategic_critique.lower()
