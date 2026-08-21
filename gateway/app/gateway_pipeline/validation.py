import json
import re

from ..clients.anthropic_client import get_client
from ..core.config import get_settings
from ..modules.base import Module
from ..schemas.context import CompletionRequest
from ..schemas.envelope import CompletionResponse
from .prompt_assembly import assemble_prompt

# Backstop only now -- see _framework_logic_check. Kept because it's free
# (no extra reasoning needed) and catches the rare case where the model's
# own self-audit misses something.
_VANITY_TERMS = {"likes", "impressions", "followers", "views", "shares", "engagement rate", "reach"}
_OUTCOME_TERMS = {
    "revenue", "pipeline", "closed-won", "closed won", "orders", "leads", "roi",
    "conversion", "win rate", "deal value", "quota", "retention", "repeat purchase",
}

_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*\s*([kKmM])?")
_NORMALIZE_RE = re.compile(r"[^a-z0-9.]+")


def _extract_number(text: str) -> float | None:
    """Pulls the first number out of `text`, expanding a trailing k/m
    suffix (e.g. "850k" -> 850000.0, "$1.2M" -> 1200000.0)."""
    match = _NUMBER_RE.search(text)
    if not match or not match.group(0).strip():
        return None
    raw = match.group(0)
    suffix = match.group(1)
    digits = raw.rstrip("kKmM \t").replace(",", "").strip()
    if not digits or digits == "-":
        return None
    try:
        value = float(digits)
    except ValueError:
        return None
    if suffix and suffix.lower() == "k":
        value *= 1_000
    elif suffix and suffix.lower() == "m":
        value *= 1_000_000
    return value


def _values_correspond(claim: str, context_value: object) -> bool:
    """Deterministic diff between a claim snippet and the context value
    it's supposedly sourced from. Handles exact/substring text matches and
    numeric matches that survive formatting differences ("$850k" in the
    claim vs. 850000 in context, or "150,000" vs. 150000)."""
    value_str = str(context_value)
    claim_norm = _NORMALIZE_RE.sub("", claim.lower())
    value_norm = _NORMALIZE_RE.sub("", value_str.lower())

    if value_norm and (value_norm in claim_norm or claim_norm in value_norm):
        return True

    claim_num = _extract_number(claim)
    value_num = _extract_number(value_str)
    if claim_num is not None and value_num is not None:
        tolerance = max(abs(value_num) * 0.01, 0.5)
        return abs(claim_num - value_num) <= tolerance

    return False


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
    """Section 3.3.2's diff-checker: for every (claim -> source_key) pair
    in sourced_fields, the source field must both exist in the hydrated
    context AND its actual value must correspond to the claim text (see
    _values_correspond) -- not just a structural key-existence check. A
    claim tagged as sourced from `deal_value` when the context's
    deal_value is a different number fails exactly like an untagged
    hallucination would."""
    context = request.context
    for claim, source_key in data["sourced_fields"].items():
        if source_key not in context:
            raise ValidationFailure(
                "grounding_check",
                f"sourced_fields claims '{claim}' came from context field "
                f"'{source_key}', which does not exist in the supplied context. "
                "Only cite fields that are actually present, or move the claim "
                "into missing_variables instead of asserting it.",
            )
        if not _values_correspond(claim, context[source_key]):
            raise ValidationFailure(
                "grounding_check",
                f"sourced_fields claims '{claim}' came from context field "
                f"'{source_key}' (actual value: {context[source_key]!r}), but "
                f"the claim text doesn't match that value. Cite the real value "
                f"exactly, or move the claim into missing_variables instead of "
                f"asserting it.",
            )


def _framework_logic_check(data: dict) -> None:
    """Section 3.3.2's semantic classifier, implemented as the model's own
    structured self-audit rather than keyword regex or a separately
    trained model: the response schema requires a `vanity_metric_audit`
    field the model must fill in as part of the SAME generation call (see
    RESPONSE_SCHEMA_INSTRUCTIONS), and this function is the Gateway's own
    deterministic enforcement of that self-report -- the model doesn't get
    to silently ignore its own audit, a failed audit forces an Invisible
    Retry exactly like any other check. This is real semantic judgment
    (the same reasoning pass that wrote the content evaluates it against
    the vanity-vs-outcome distinction) without a second API round-trip or
    a trained classifier, and it correctly handles both false-positive
    cases from the old keyword approach ("the Plant Manager likes fast
    turnaround") and false-negative ones (an impressions-obsessed strategy
    that never uses the word "impressions").

    _VANITY_TERMS/_OUTCOME_TERMS below now run only as a backstop when the
    audit field is missing or malformed (e.g. a fake/legacy test fixture,
    or a model response that skipped it) -- English-only, so for non-
    English traffic without a valid audit field this backstop is a silent
    no-op rather than a misfire. The primary path (the self-audit) has no
    such language limitation since it's the model's own judgment in
    whatever language it's already responding in."""
    audit = data.get("vanity_metric_audit")
    if isinstance(audit, dict) and isinstance(audit.get("leans_on_vanity_metrics"), bool):
        if audit["leans_on_vanity_metrics"]:
            reasoning = audit.get("reasoning", "no reasoning supplied")
            raise ValidationFailure(
                "framework_logic_check",
                f"Your own vanity_metric_audit flagged this response: {reasoning} "
                "Reframe around a measurable business outcome (revenue, pipeline, "
                "orders, leads, retention) instead.",
            )
        return

    combined = f"{data['generated_content']} {data['strategic_critique']}".lower()
    has_vanity_term = any(term in combined for term in _VANITY_TERMS)
    has_outcome_term = any(term in combined for term in _OUTCOME_TERMS)

    if has_vanity_term and not has_outcome_term:
        raise ValidationFailure(
            "framework_logic_check",
            "Response leans on vanity-metric language (likes/impressions/"
            "followers/etc.) with no outcome framing (revenue/pipeline/leads/"
            "orders/etc.) anywhere in the response, and no vanity_metric_audit "
            "field was supplied to judge it directly. Reframe around a "
            "measurable business outcome and include the audit field.",
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
