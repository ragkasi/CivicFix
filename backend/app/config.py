from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/civicfix"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""
    supabase_storage_bucket: str = "report-images"

    # AI (placeholders — wired in Phase 4)
    openai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    vision_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"

    # App
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    resident_app_url: str = "http://localhost:3000"
    admin_app_url: str = "http://localhost:3000/admin"

    # Notifications (placeholders — wired in Phase 6)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    email_api_key: str = ""
    email_from: str = "no-reply@civicfix.local"

    # MCP
    mcp_server_name: str = "city-ops-mcp"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
