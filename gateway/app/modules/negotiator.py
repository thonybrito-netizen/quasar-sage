from ..schemas.context import CompletionRequest
from .base import Module


class NegotiatorModule(Module):
    """STUB for launch. See dealmaker.py for the pattern this follows."""

    module_id = "negotiator"
    live = False
    theme_color = "#8B5CF6"  # violet, Section 2.4.3

    def system_prompt(self, request: CompletionRequest) -> str:
        raise NotImplementedError("Negotiator is not live this sprint")

    def fallback_strategic_critique(self, request: CompletionRequest) -> str:
        return (
            "The Negotiator module is not enabled yet -- it's on the "
            "roadmap after launch. Try Visionary or Storyteller for now."
        )
