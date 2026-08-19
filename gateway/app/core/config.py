import json
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Gateway configuration. See gateway/.env.example for the full list.

    TENANT_API_KEYS is a JSON object mapping tenant_id -> bearer key, e.g.
    {"quietnoise": "qns_...", "lorito": "col_..."}. This is deliberately a
    static env-configured map rather than the DB-backed multi-tenant model
    from spec Section 7.2 -- that model is Phase-3 (Sage-as-a-Service)
    scope, out of range for this sprint.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str | None = None
    vertex_project_id: str | None = None
    vertex_region: str = "global"
    chat_model_id: str = "claude-sonnet-5"

    max_invisible_retries: int = 2

    tenant_api_keys_json: str = Field(default="{}", validation_alias="TENANT_API_KEYS")
    cors_allow_origins_csv: str = Field(default="*", validation_alias="CORS_ALLOW_ORIGINS")

    @property
    def tenant_api_keys(self) -> dict[str, str]:
        return json.loads(self.tenant_api_keys_json)

    @property
    def cors_allow_origins(self) -> list[str]:
        if self.cors_allow_origins_csv == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins_csv.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
