from fastapi import APIRouter, Depends

from ..core.security import verify_tenant_api_key
from ..modules.registry import list_modules

router = APIRouter(prefix="/v1", tags=["modules"])


@router.get("/modules")
async def get_modules(tenant_id: str = Depends(verify_tenant_api_key)) -> list[dict]:
    """Section 7.1's GET /v1/modules, simplified: every tenant currently
    sees every module (no plan-tier entitlement table this sprint), with
    `live` telling the caller which ones will actually generate content
    vs. return the roadmap fallback."""
    return [
        {"module_id": module.module_id, "live": module.live, "theme_color": module.theme_color}
        for module in list_modules()
    ]
