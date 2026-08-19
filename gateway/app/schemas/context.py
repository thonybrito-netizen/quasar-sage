from typing import Any, Literal

from pydantic import BaseModel, Field

ModuleId = Literal["visionary", "storyteller", "dealmaker", "negotiator", "locker_room"]
DealmakerMode = Literal["enterprise", "retail"]
Language = Literal["en", "es", "pt"]


class ContextPayload(BaseModel):
    """The 'Payload Context' block from spec Section 3.1.1.

    `context` is intentionally a free-form dict rather than a rigid schema:
    QuietNoise's context (marketing-agency fields like client goals,
    strategy summary) and Lorito's context (CRM fields like deal_size,
    pipeline_stage) are shaped very differently, and the two live modules
    (Visionary, Storyteller) don't need a tight CRM schema to do their job.
    Every key in `context` is treated as untrusted free text per Section
    3.1.2 -- see gateway_pipeline/untrusted_context.py.

    `language` is driven by the calling app's own current UI language
    (QuietNoise's LanguageContext, Lorito's Spanish-only convention) rather
    than inferred or offered as a separate widget setting -- a co-pilot
    answering in the wrong language next to the host app's own chrome
    would read as broken, and a second language picker inside the widget
    would just be a redundant, confusing control.
    """

    module: ModuleId
    mode: DealmakerMode | None = None
    language: Language = "en"
    user_message: str = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class CompletionRequest(BaseModel):
    tenant_id: str | None = None  # set by the auth dependency, not the caller
    module: ModuleId
    mode: DealmakerMode | None = None
    language: Language = "en"
    user_message: str = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
