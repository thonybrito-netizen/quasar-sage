from .base import Module
from .dealmaker import DealmakerModule
from .locker_room import LockerRoomModule
from .negotiator import NegotiatorModule
from .storyteller import StorytellerModule
from .visionary import VisionaryModule

_MODULES: dict[str, Module] = {
    "visionary": VisionaryModule(),
    "storyteller": StorytellerModule(),
    "dealmaker": DealmakerModule(),
    "negotiator": NegotiatorModule(),
    "locker_room": LockerRoomModule(),
}


def get_module(module_id: str) -> Module:
    try:
        return _MODULES[module_id]
    except KeyError as exc:
        raise ValueError(f"Unknown module_id: {module_id!r}") from exc


def list_modules() -> list[Module]:
    return list(_MODULES.values())
