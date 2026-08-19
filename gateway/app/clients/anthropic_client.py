from typing import Optional, Union

from anthropic import Anthropic, AnthropicVertex

from ..core.config import get_settings

_client: Optional[Union[Anthropic, AnthropicVertex]] = None


def get_client() -> Union[Anthropic, AnthropicVertex]:
    """Direct Anthropic API (ANTHROPIC_API_KEY) if a key is configured --
    bypasses Vertex/GCP entirely, including its per-project quota approval
    step. Falls back to AnthropicVertex (Google Cloud credentials) if no
    key is set. Ported from executive-coach's backend/app/chat.py
    (_get_client()), which hit and solved this exact problem: Vertex AI's
    default quota for Anthropic models is 0 on a fresh GCP project and
    can't be self-served, so a fresh project needs the direct-API path.
    """
    global _client
    if _client is None:
        settings = get_settings()
        if settings.anthropic_api_key:
            _client = Anthropic(api_key=settings.anthropic_api_key)
        else:
            if not settings.vertex_project_id:
                raise RuntimeError(
                    "No ANTHROPIC_API_KEY and no VERTEX_PROJECT_ID configured -- "
                    "the Gateway has no way to reach Claude."
                )
            _client = AnthropicVertex(project_id=settings.vertex_project_id, region=settings.vertex_region)
    return _client


def reset_client_for_tests() -> None:
    global _client
    _client = None
