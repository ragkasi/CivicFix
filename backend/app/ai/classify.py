"""Report classification using the OpenAI API (GPT-4o with optional vision)."""
import json
import logging

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

# ─── Valid values ──────────────────────────────────────────────────────────────

VALID_CATEGORIES = {
    "pothole", "streetlight", "flooding", "sidewalk_damage",
    "trash_overflow", "damaged_sign", "road_hazard", "graffiti",
    "snow_or_ice", "other",
}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_DEPT_SLUGS = {
    "public_works", "transportation", "sanitation", "parks_and_recreation",
    "water_and_drainage", "code_enforcement", "general_services",
}

# ─── Fallback (used when API is unavailable or output is invalid) ─────────────

FALLBACK: dict = {
    "category": "other",
    "severity": "medium",
    "department_slug": "general_services",
    "summary": "Resident submitted a report that requires manual review.",
    "recommended_action": "Review the report details and assign the appropriate department.",
    "confidence": 0.0,
}

# ─── System prompt ────────────────────────────────────────────────────────────

_SYSTEM = """\
You are an AI assistant for a city civic issue reporting system.
Classify resident infrastructure reports and route them to the correct department.

Respond ONLY with valid JSON — no prose, no markdown fences:
{
  "category": "<one of: pothole|streetlight|flooding|sidewalk_damage|trash_overflow|damaged_sign|road_hazard|graffiti|snow_or_ice|other>",
  "severity": "<one of: low|medium|high|critical>",
  "department_slug": "<one of: public_works|transportation|sanitation|parks_and_recreation|water_and_drainage|code_enforcement|general_services>",
  "summary": "<2-3 sentence admin-facing summary of the issue>",
  "recommended_action": "<brief recommended next step for city staff>",
  "confidence": <float 0.0-1.0>
}

Severity guide:
- low: cosmetic or non-urgent
- medium: moderate inconvenience or gradual worsening
- high: safety risk or access blockage
- critical: immediate danger or major infrastructure failure

Department routing guide:
- public_works: potholes, road damage, sidewalks, drainage, snow/ice
- transportation: traffic signals, road signs
- sanitation: trash, graffiti
- parks_and_recreation: parks, trees
- water_and_drainage: water main, storm drains, flood
- code_enforcement: zoning, blight, nuisance
- general_services: anything else
"""


# ─── Public API ───────────────────────────────────────────────────────────────


async def classify_report(
    description: str,
    image_url: str | None = None,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Classify a civic report with GPT-4o.

    Returns a validated classification dict. Falls back to FALLBACK values
    if the API is unavailable or returns invalid output.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set — returning AI fallback classification")
        return FALLBACK.copy()

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Build user text
    parts = [f"Description: {description}"]
    if address:
        parts.append(f"Location: {address}")
    elif latitude is not None and longitude is not None:
        parts.append(f"Coordinates: {latitude:.4f}, {longitude:.4f}")
    user_text = "\n".join(parts)

    # Compose message content — include image if available
    if image_url:
        content: list | str = [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": image_url, "detail": "low"}},
        ]
    else:
        content = user_text

    try:
        response = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": content},
            ],
            max_tokens=512,
            temperature=0.1,
        )
        raw = response.choices[0].message.content or ""
        return validate_classification(raw)

    except Exception as exc:
        logger.error(f"OpenAI classification request failed: {exc}")
        return FALLBACK.copy()


def validate_classification(raw: str) -> dict:
    """Parse and validate raw AI JSON output.

    Returns FALLBACK if the output is malformed or contains invalid values.
    This function is kept pure (no I/O) so it is easy to unit-test.
    """
    try:
        text = raw.strip()
        # Strip markdown fences if the model wraps output despite the prompt
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1])

        data = json.loads(text)

        category = data.get("category", "")
        severity = data.get("severity", "")
        dept_slug = data.get("department_slug", "")
        confidence = float(data.get("confidence", -1))
        summary = str(data.get("summary", "")).strip()
        recommended_action = str(data.get("recommended_action", "")).strip()

        if category not in VALID_CATEGORIES:
            raise ValueError(f"Unknown category: {category!r}")
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"Unknown severity: {severity!r}")
        if dept_slug not in VALID_DEPT_SLUGS:
            raise ValueError(f"Unknown department_slug: {dept_slug!r}")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"confidence out of range: {confidence}")
        if not summary:
            raise ValueError("summary is empty")
        if not recommended_action:
            raise ValueError("recommended_action is empty")

        return {
            "category": category,
            "severity": severity,
            "department_slug": dept_slug,
            "summary": summary,
            "recommended_action": recommended_action,
            "confidence": confidence,
        }

    except Exception as exc:
        logger.warning(f"AI output validation failed ({exc}); using fallback")
        return FALLBACK.copy()
