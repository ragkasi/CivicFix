from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache(maxsize=1)
def _build_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_supabase_client() -> Client:
    """Return a cached Supabase service-role client.

    Raises RuntimeError when SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY are
    not set, so callers get a clear message instead of an opaque SDK error.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env "
            "before using the Supabase client. Copy .env.example and fill in your "
            "Supabase project credentials."
        )
    return _build_client()
