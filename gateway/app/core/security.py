from fastapi import Header, HTTPException

from .config import get_settings


async def verify_tenant_api_key(authorization: str = Header(..., alias="Authorization")) -> str:
    """Resolves a Bearer token to a tenant_id, or rejects the request.

    Modeled on QuietNoise's require_colibri_api_key dependency
    (python-backend/app/dependencies.py): a single static bearer-token
    check per caller, no DB lookup. Sage has one key per tenant rather
    than one key overall, so this returns the resolved tenant_id for
    downstream handlers to use.
    """
    settings = get_settings()
    tenant_api_keys = settings.tenant_api_keys
    if not tenant_api_keys:
        raise HTTPException(status_code=503, detail="Gateway has no tenant API keys configured")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Expected 'Authorization: Bearer <key>'")

    for tenant_id, key in tenant_api_keys.items():
        if token == key:
            return tenant_id

    raise HTTPException(status_code=401, detail="Invalid API key")
