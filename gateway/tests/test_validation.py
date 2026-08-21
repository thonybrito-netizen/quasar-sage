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

MISMATCHED_VALUE_RESPONSE = json.dumps(
    {
        "missing_variables": [],
        "strategic_critique": "Solid, ship it.",
        "generated_content": "Chevron's $850k deal closes Friday.",
        "suggested_next_action": None,
        # deal_value IS in context (see _request(context=...) below), but the
        # claimed figure doesn't match its real value -- key exists, value doesn't.
        "sourced_fields": {"$850k": "deal_value"},
    }
)

VANITY_AUDIT_TRUE_RESPONSE = json.dumps(
    {
        "missing_variables": [],
        "strategic_critique": "This post is going to blow up.",
        "generated_content": "Focus on getting more likes and followers this quarter.",
        "suggested_next_action": None,
        "sourced_fields": {},
        "vanity_metric_audit": {
            "leans_on_vanity_metrics": True,
            "reasoning": "Treats likes/followers as the goal itself, no outcome framing anywhere.",
        },
    }
)

VANITY_AUDIT_FALSE_RESPONSE = json.dumps(
    {
        "missing_variables": [],
        "strategic_critique": "The Plant Manager likes fast turnaround, so lead with that.",
        "generated_content": "Faster turnaround wins renewals, not likes.",
        "suggested_next_action": None,
        "sourced_fields": {},
        "vanity_metric_audit": {
            "leans_on_vanity_metrics": False,
            "reasoning": "'likes' here describes a stakeholder preference, not a vanity metric being cited as success.",
        },
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


def test_grounding_check_rejects_value_mismatch_even_when_key_exists(fake_claude):
    # Regression test for the real diff-checker (not just key-existence):
    # deal_value is genuinely in context, but the claimed figure is wrong.
    fake_claude([MISMATCHED_VALUE_RESPONSE, VALID_RESPONSE])
    result = generate_completion(VisionaryModule(), _request(context={"deal_value": 150000}))
    assert result.resolved_via == "invisible_retry"


def test_grounding_check_accepts_matching_value(fake_claude):
    matching_response = json.dumps(
        {
            "missing_variables": [],
            "strategic_critique": "Solid, ship it.",
            "generated_content": "Chevron's $150,000 deal closes Friday.",
            "suggested_next_action": None,
            "sourced_fields": {"$150,000": "deal_value"},
        }
    )
    fake_claude([matching_response])
    result = generate_completion(VisionaryModule(), _request(context={"deal_value": 150000}))
    assert result.resolved_via == "first_attempt"


def test_vanity_metric_self_audit_true_triggers_retry(fake_claude):
    fake_claude([VANITY_AUDIT_TRUE_RESPONSE, VALID_RESPONSE])
    result = generate_completion(VisionaryModule(), _request())
    assert result.resolved_via == "invisible_retry"


def test_vanity_metric_self_audit_false_is_not_a_false_positive(fake_claude):
    # This is exactly the false-positive case the old keyword regex got
    # wrong (spec Section 5.5): "likes" appears, but as a stakeholder
    # preference, not a vanity metric -- the model's own audit says so and
    # the Gateway trusts that judgment instead of pattern-matching the word.
    fake_claude([VANITY_AUDIT_FALSE_RESPONSE])
    result = generate_completion(VisionaryModule(), _request())
    assert result.resolved_via == "first_attempt"


def test_graceful_fallback_when_no_model_backend_configured(monkeypatch, env_setup):
    # Explicitly empty, not delenv: an OS env var (even "") outranks the
    # .env file in pydantic-settings' source precedence, but merely
    # deleting the OS var lets it fall through to gateway/.env's real key
    # (present there for manual local testing) -- which would make this a
    # real, slow API call instead of testing the "not configured" path.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
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
