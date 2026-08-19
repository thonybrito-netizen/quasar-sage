from ..schemas.context import CompletionRequest
from .base import Module


class DealmakerModule(Module):
    """STUB for launch. Accepts a `mode` (enterprise/retail) per spec
    Section 2.3.2 so callers can already build UI against the real
    contract, but never calls Claude -- the Stakeholder Map / Trigger
    Stack rulesets are not implemented yet. Real code, correct envelope
    shape, deliberately no generation."""

    module_id = "dealmaker"
    live = False
    theme_color = "#22C55E"  # green (enterprise) / green-gold (retail), Section 6

    def system_prompt(self, request: CompletionRequest) -> str:
        raise NotImplementedError("Dealmaker is not live this sprint")

    def fallback_strategic_critique(self, request: CompletionRequest) -> str:
        mode = request.mode or "enterprise"
        return (
            f"The Dealmaker module ({mode} mode) is not enabled yet -- "
            "it's on the roadmap after launch. Try Visionary or Storyteller "
            "for now."
        )
