"""Embedding generation using the OpenAI embeddings API."""
import logging

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


def build_embedding_text(
    description: str,
    category: str | None = None,
    severity: str | None = None,
    address: str | None = None,
    summary: str | None = None,
) -> str:
    """Concatenate report fields into a single string for embedding.

    Kept as a pure function so tests can verify the output without I/O.
    """
    parts = [description]
    if category:
        parts.append(category)
    if severity:
        parts.append(severity)
    if address:
        parts.append(address)
    if summary:
        parts.append(summary)
    return " | ".join(parts)


async def generate_embedding(text: str) -> list[float] | None:
    """Generate a 1536-dimensional embedding using text-embedding-3-small.

    Returns None when OPENAI_API_KEY is not configured or the call fails.
    Callers should handle None gracefully (skip storage rather than crash).
    """
    settings = get_settings()

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set — skipping embedding generation")
        return None

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    except Exception as exc:
        logger.error(f"Embedding generation failed: {exc}")
        return None
