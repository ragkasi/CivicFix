import asyncio
import uuid as _uuid
from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache(maxsize=1)
def _build_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_supabase_client() -> Client:
    """Return a cached Supabase service-role client.

    Raises RuntimeError when credentials are missing so callers get a clear
    message instead of an opaque SDK error.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env. "
            "Copy .env.example and fill in your Supabase project credentials."
        )
    return _build_client()


async def upload_report_image(
    file_bytes: bytes, filename: str, content_type: str
) -> dict:
    """Upload an image to Supabase Storage and return its path and public URL.

    Args:
        file_bytes:   Raw file content.
        filename:     Original filename (used only to infer the extension).
        content_type: MIME type, e.g. "image/jpeg".

    Returns:
        {"storage_path": "reports/uuid.jpg", "public_url": "https://..."}

    Raises:
        RuntimeError: When Supabase credentials or storage bucket are missing.
    """
    settings = get_settings()
    if not settings.supabase_storage_bucket:
        raise RuntimeError(
            "SUPABASE_STORAGE_BUCKET is not configured. "
            "Set it in backend/.env (default: report-images)."
        )

    client = get_supabase_client()

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    storage_path = f"reports/{_uuid.uuid4()}.{ext}"
    bucket = settings.supabase_storage_bucket

    def _upload():
        return client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type},
        )

    await asyncio.to_thread(_upload)

    # get_public_url is a URL construction — no network call needed
    public_url = client.storage.from_(bucket).get_public_url(storage_path)

    return {"storage_path": storage_path, "public_url": public_url}
