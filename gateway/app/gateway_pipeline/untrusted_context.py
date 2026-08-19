import re
from typing import Any

# Patterns that look like an attempt to redirect the model rather than
# describe business context. Matches are stripped, not escaped -- the
# field still reaches the model as reference data, just without the
# instruction-like phrase. This is a basic heuristic scrub (spec Section
# 3.1.2), not a full prompt-injection classifier.
_INSTRUCTION_LIKE_PATTERNS = [
    re.compile(r"ignore (all|any|the)?\s*(previous|prior|above)\s*instructions", re.IGNORECASE),
    re.compile(r"disregard (all|any|the)?\s*(previous|prior|above)\s*instructions", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"new instructions\s*:", re.IGNORECASE),
]


def sanitize_text(value: str) -> str:
    cleaned = value
    for pattern in _INSTRUCTION_LIKE_PATTERNS:
        cleaned = pattern.sub("[redacted]", cleaned)
    return cleaned


def sanitize_context(context: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitizes string values in a context payload. Non-string
    values (numbers, bools) pass through untouched -- they can't carry an
    instruction-like phrase."""
    sanitized: dict[str, Any] = {}
    for key, value in context.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_text(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_context(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_text(v) if isinstance(v, str) else v for v in value]
        else:
            sanitized[key] = value
    return sanitized


def render_context_block(context: dict[str, Any]) -> str:
    """Wraps sanitized context fields in explicit delimiters, passed to the
    model as reference content -- never concatenated into the same
    instruction channel as the Core Identity or Active Module blocks."""
    if not context:
        return "<context_fields>\n(none supplied)\n</context_fields>"

    lines = ["<context_fields>"]
    for key, value in sanitize_context(context).items():
        lines.append(f'  <context_field key="{key}">{value}</context_field>')
    lines.append("</context_fields>")
    return "\n".join(lines)
