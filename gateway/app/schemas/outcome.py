from typing import Literal

from pydantic import BaseModel, Field

OutcomeLabel = Literal["accepted", "rejected"]


class OutcomeEvent(BaseModel):
    """Section 4.3.1's Outcome-Only Persistence: the Gateway never sees or
    stores the raw draft/edit text (that stays solely in the host
    platform's own database, per Section 4.2's Data Retention Ownership)
    -- only this minimal structural reference, once the host app has
    computed the accepted/rejected delta itself and is reporting the
    result."""

    module: str
    mode: str | None = None
    field_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="What kind of content this was, e.g. 'positioning_statement', 'email_draft', 'opening_hook'.",
    )
    label: OutcomeLabel
