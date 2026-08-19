from pydantic import BaseModel, Field


class CompletionResponse(BaseModel):
    """The JSON Response Envelope, spec Section 3.3.1.

    This is the one contract every caller (QuietNoise, Lorito, and any
    future tenant) gets back regardless of module or Mode -- it's what
    lets the client apps render deterministic UI (unlock buttons, populate
    OKR trackers) instead of parsing free text.
    """

    missing_variables: list[str] = Field(default_factory=list)
    strategic_critique: str
    generated_content: str
    suggested_next_action: str | None = None
    sourced_fields: dict[str, str] = Field(default_factory=dict)

    resolved_via: str = "first_attempt"  # "first_attempt" | "invisible_retry" | "graceful_fallback"
    module: str
    mode: str | None = None
