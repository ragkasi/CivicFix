from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import departments, reports, tracking, upload

settings = get_settings()

app = FastAPI(
    title="CivicFix API",
    version="0.1.0",
    description="AI-powered civic issue reporting and routing platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(departments.router, prefix="/api/departments", tags=["departments"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["tracking"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "version": app.version}
