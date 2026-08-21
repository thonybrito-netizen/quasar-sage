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
  "sourced_fields": { [claimKeyword: string]: string },  // maps a factual \
claim to the context_field key it was sourced from -- the claim text must \
match the field's actual value (a diff-checker rejects mismatches)
  "vanity_metric_audit": {
    "leans_on_vanity_metrics": boolean,  // true only if generated_content \
or strategic_critique treats likes/impressions/followers/reach/views as \
evidence of success on their own, with no outcome framing (revenue, \
pipeline, orders, leads, retention, conversion) anywhere in the response. \
A mention of one of those words in a non-metric sense (e.g. "the Plant \
Manager likes fast turnaround") is NOT a vanity-metric lean -- judge \
intent, not literal word presence.
    "reasoning": string  // one sentence justifying the boolean above
  }
}
Self-audit honestly: this field is checked by code, not trusted blindly \
-- a true value here triggers a mandatory rewrite, so getting it right \
the first time is faster than being caught by the retry.
"""

_LANGUAGE_NAMES = {"en": "English", "es": "Spanish", "pt": "Portuguese"}


def _language_instruction(language: str) -> str:
    name = _LANGUAGE_NAMES.get(language, language)
    return (
        f"Write in {name}: the strategic_critique text, generated_content, "
        f"every missing_variables entry, and suggested_next_action must all "
        f"be in {name}. The JSON keys themselves (missing_variables, "
        f"strategic_critique, etc.) are a fixed machine contract and stay "
        f"in English exactly as shown above -- only the string values you "
        f"write into them change language."
    )


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
    system_prompt = "\n\n".join(
        [
            CORE_IDENTITY,
            module.system_prompt(request),
            RESPONSE_SCHEMA_INSTRUCTIONS,
            _language_instruction(request.language),
        ]
    )
    user_content = "\n\n".join(
        [render_context_block(request.context), f"<user_message>\n{request.user_message}\n</user_message>"]
    )
    return system_prompt, user_content
