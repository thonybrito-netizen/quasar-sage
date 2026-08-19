from fastapi import APIRouter, Depends

from ..core.security import verify_tenant_api_key
from ..gateway_pipeline.intent_router import route
from ..gateway_pipeline.validation import generate_completion
from ..schemas.context import CompletionRequest, ContextPayload
from ..schemas.envelope import CompletionResponse

router = APIRouter(prefix="/v1", tags=["completions"])


@router.post("/completions", response_model=CompletionResponse)
async def create_completion(
    payload: ContextPayload,
    tenant_id: str = Depends(verify_tenant_api_key),
) -> CompletionResponse:
    request = CompletionRequest(
        tenant_id=tenant_id,
        module=payload.module,
        mode=payload.mode,
        user_message=payload.user_message,
        context=payload.context,
    )
    module = route(request)
    return generate_completion(module, request)
