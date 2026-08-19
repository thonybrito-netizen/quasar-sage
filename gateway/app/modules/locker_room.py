from ..schemas.context import CompletionRequest
from .base import Module


class LockerRoomModule(Module):
    """STUB for launch. See dealmaker.py for the pattern this follows."""

    module_id = "locker_room"
    live = False
    theme_color = "#EF4444"  # red/black, Section 2.5.3

    def system_prompt(self, request: CompletionRequest) -> str:
        raise NotImplementedError("Locker Room is not live this sprint")

    def fallback_strategic_critique(self, request: CompletionRequest) -> str:
        return (
            "The Locker Room module is not enabled yet -- it's on the "
            "roadmap after launch. Try Visionary or Storyteller for now."
        )
