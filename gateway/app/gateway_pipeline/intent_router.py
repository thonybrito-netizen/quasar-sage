from fastapi import HTTPException

from ..modules.base import Module
from ..modules.registry import get_module
from ..schemas.context import CompletionRequest


def route(request: CompletionRequest) -> Module:
    """Section 3.2: explicit routing only for this sprint. `module_id` is
    required on every request (enforced by CompletionRequest's schema) and
    honored directly. The implicit NLP micro-classifier (Section 3.2.2,
    for a generic command-palette text box with no module pre-selected) is
    deferred -- every caller this sprint already knows which module button
    the user clicked."""
    try:
        return get_module(request.module)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
