import json

from ..clients.anthropic_client import get_client
from ..core.config import get_settings
from ..modules.base import Module
from ..schemas.context import CompletionRequest
from ..schemas.envelope import CompletionResponse
from .prompt_assembly import assemble_prompt

_VANITY_TERMS = {"likes", "impressions", "followers", "views", "shares", "engagement rate", "reach"}
_OUTCOME_TERMS = {
    "revenue", "pipeline", "closed-won", "closed won", "orders", "leads", "roi",
    "conversion", "win rate", "deal value", "quota", "retention", "repeat purchase",
}


class ValidationFailure(Exception):
    """Raised by a validation stage. `rule` names the stage, and is cited
    back to the model verbatim in the Invisible Retry follow-up (Section
    3.3.2) so the correction is specific, not generic."""

    def __init__(self, rule: str, message: str):
        self.rule = rule
        self.message = message
        super().__init__(message)


def _type_validate(raw_text: str) -> dict:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValidationFailure("type_validation", f"Response was not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValidationFailure("type_validation", "Response JSON must be an object")

    required = {"missing_variables", "strategic_critique", "generated_content", "sourced_fields"}
    missing = required - data.keys()
    if missing:
        raise ValidationFailure("type_validation", f"Response is missing required keys: {sorted(missing)}")
    if not isinstance(data["missing_variables"], list):
        raise ValidationFailure("type_validation", "missing_variables must be an array")
    if not isinstance(data["sourced_fields"], dict):
        raise ValidationFailure("type_validation", "sourced_fields must be an object")
    if not isinstance(data["strategic_critique"], str) or not isinstance(data["generated_content"], str):
        raise ValidationFailure("type_validation", "strategic_critique and generated_content must be strings")
    return data


def _grounding_check(data: dict, request: CompletionRequest) -> None:
    """Simplified vs. spec Section 3.3.2: verifies every sourced_fields key
    names a field that actually exists in the hydrated context payload
    (structural match), rather than running a full semantic diff between
    the claim text and the field value."""
    context_keys = set(request.context.keys())
    for claim, source_key in data["sourced_fields"].items():
        if source_key not in context_keys:
            raise ValidationFailure(
                "grounding_check",
                f"sourced_fields claims '{claim}' came from context field "
                f"'{source_key}', which does not exist in the supplied context. "
                "Only cite fields that are actually present, or move the claim "
                "into missing_variables instead of asserting it.",
            )


def _framework_logic_check(data: dict) -> None:
    """Simplified vs. spec Section 3.3.2: a keyword heuristic, not a
    trained semantic classifier. Flags content that leans on vanity-metric
    language with no outcome framing anywhere in the same response."""
    combined = f"{data['generated_content']} {data['strategic_critique']}".lower()
    has_vanity_term = any(term in combined for term in _VANITY_TERMS)
    has_outcome_term = any(term in combined for term in _OUTCOME_TERMS)

    if has_vanity_term and not has_outcome_term:
        raise ValidationFailure(
            "framework_logic_check",
            "Response leans on vanity-metric language (likes/impressions/"
            "followers/etc.) with no outcome framing (revenue/pipeline/leads/"
            "orders/etc.) anywhere in the response. Reframe around a "
            "measurable business outcome.",
        )


def _run_checks(raw_text: str, request: CompletionRequest) -> dict:
    data = _type_validate(raw_text)
    _grounding_check(data, request)
    _framework_logic_check(data)
    return data


def _call_model(system_prompt: str, user_content: str) -> str:
    settings = get_settings()
    client = get_client()
    response = client.messages.create(
        model=settings.chat_model_id,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def generate_completion(module: Module, request: CompletionRequest) -> CompletionResponse:
    """Runs the full outbound flow: prompt assembly -> generation ->
    Middleware Validation Sequence -> Invisible Retry (up to
    max_invisible_retries) -> Graceful Fallback (Section 3.3.2)."""
    if not module.live:
        return CompletionResponse(
            missing_variables=[],
            strategic_critique=module.fallback_strategic_critique(request),
            generated_content="",
            suggested_next_action=None,
            sourced_fields={},
            resolved_via="graceful_fallback",
            module=module.module_id,
            mode=request.mode,
        )

    settings = get_settings()

    if not settings.anthropic_api_key and not settings.vertex_project_id:
        # No model backend configured at all -- fail clean rather than
        # letting anthropic_client.get_client()'s RuntimeError surface as
        # an unhandled 500. Distinct message from the module's own
        # fallback_strategic_critique so this misconfiguration is
        # distinguishable from "validation kept failing" in logs/UI.
        return CompletionResponse(
            missing_variables=[],
            strategic_critique=(
                "Quasar Sage has no model backend configured yet "
                "(ANTHROPIC_API_KEY / VERTEX_PROJECT_ID are both unset on the Gateway)."
            ),
            generated_content="",
            suggested_next_action=None,
            sourced_fields={},
            resolved_via="graceful_fallback",
            module=module.module_id,
            mode=request.mode,
        )

    system_prompt, user_content = assemble_prompt(module, request)

    attempts = 0
    max_attempts = 1 + settings.max_invisible_retries
    last_failure: ValidationFailure | None = None

    while attempts < max_attempts:
        if attempts > 0 and last_failure is not None:
            user_content = (
                f"{user_content}\n\n<validation_retry>\n"
                f"Your previous response failed the {last_failure.rule} check: "
                f"{last_failure.message}\nRegenerate a corrected response.\n"
                f"</validation_retry>"
            )
        raw_text = _call_model(system_prompt, user_content)
        try:
            data = _run_checks(raw_text, request)
            return CompletionResponse(
                missing_variables=data["missing_variables"],
                strategic_critique=data["strategic_critique"],
                generated_content=data["generated_content"],
                suggested_next_action=data.get("suggested_next_action"),
                sourced_fields=data["sourced_fields"],
                resolved_via="first_attempt" if attempts == 0 else "invisible_retry",
                module=module.module_id,
                mode=request.mode,
            )
        except ValidationFailure as failure:
            last_failure = failure
            attempts += 1

    # Graceful Fallback: two invisible retries both failed validation.
    return CompletionResponse(
        missing_variables=[],
        strategic_critique=module.fallback_strategic_critique(request),
        generated_content="",
        suggested_next_action=None,
        sourced_fields={},
        resolved_via="graceful_fallback",
        module=module.module_id,
        mode=request.mode,
    )
