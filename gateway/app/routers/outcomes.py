from fastapi import APIRouter, Depends, HTTPException, status

from ..clients.outcome_store import write_outcome
from ..core.security import verify_tenant_api_key
from ..schemas.outcome import OutcomeEvent

router = APIRouter(prefix="/v1", tags=["outcomes"])


@router.post("/outcomes", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def record_outcome(
    payload: OutcomeEvent,
    tenant_id: str = Depends(verify_tenant_api_key),
) -> None:
    """Section 4.3.1's Outcome-Only Persistence endpoint.

    Not yet called by either host app -- QuietNoise/Lorito would need to
    detect when a user finalizes or edits Sage-generated content and
    report the resulting accepted/rejected delta here themselves (the
    Gateway has no visibility into what happens to generated_content
    after it returns the response; per Section 4.2 it never should).
    Scaffolded and tested so wiring this in later is additive integration
    work in each host app, not a new Gateway feature to build first.
    """
    try:
        write_outcome(tenant_id, payload.module, payload.mode, payload.field_type, payload.label)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not record outcome: {exc}",
        ) from exc
