from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db.supabase import upload_report_image

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload a report image to Supabase Storage.

    Returns the storage path and public URL to include in the report creation
    request body as image_path.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_TYPES))}",
        )

    content = await file.read()

    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content) // 1024} KB). Maximum is 10 MB.",
        )

    try:
        result = await upload_report_image(
            content,
            file.filename or "upload.jpg",
            file.content_type or "image/jpeg",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return result
