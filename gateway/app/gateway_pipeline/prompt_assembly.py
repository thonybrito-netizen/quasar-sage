from ..modules.base import CORE_IDENTITY, Module
from ..schemas.context import CompletionRequest
from .untrusted_context import render_context_block

RESPONSE_SCHEMA_INSTRUCTIONS = """Return exactly this JSON shape, nothing \
else:
{
  "missing_variables": string[],
  "strategic_critique": string,
  "generated_content": string,
  "suggested_next_action": string | null,
  "sourced_fields": { [claimKeyword: string]: string }  // maps a factual \
claim to the context_field key it was sourced from
}
"""


def assemble_prompt(module: Module, request: CompletionRequest) -> tuple[str, str]:
    """Section 3.1.1's three-block Modular Assembly Process: Core Identity
    (static) + Active Module (dynamic) form the instruction channel;
    Payload Context (dynamic, untrusted) forms the content channel. These
    are kept on Claude's separate `system` and `user` channels rather than
    concatenated into one string, per Section 3.1.2's Delimiter & Role
    Separation requirement -- context data can never masquerade as an
    instruction because it's never in the instruction channel at all.

    Returns (system_prompt, user_content).
    """
    system_prompt = "\n\n".join([CORE_IDENTITY, module.system_prompt(request), RESPONSE_SCHEMA_INSTRUCTIONS])
    user_content = "\n\n".join(
        [render_context_block(request.context), f"<user_message>\n{request.user_message}\n</user_message>"]
    )
    return system_prompt, user_content
