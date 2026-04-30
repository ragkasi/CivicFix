"""AI pipeline tests.

All tests in this file run WITHOUT calling the real OpenAI API.
- validate_classification and build_embedding_text are pure functions — tested directly.
- classify_report and generate_embedding calls are mocked via unittest.mock.patch.
- Optional integration tests (marked with _requires_key) skip when OPENAI_API_KEY is missing.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.ai.classify import FALLBACK, validate_classification
from app.ai.embeddings import build_embedding_text
from app.config import get_settings

_settings = get_settings()
_has_openai_key = bool(_settings.openai_api_key)
_requires_key = pytest.mark.skipif(
    not _has_openai_key,
    reason="OPENAI_API_KEY not configured — skipping real AI tests",
)


# ─── validate_classification — pure function tests ────────────────────────────


def test_validate_valid_output():
    raw = json.dumps({
        "category": "flooding",
        "severity": "high",
        "department_slug": "public_works",
        "summary": "Recurring sidewalk flooding near bus stop after rainfall.",
        "recommended_action": "Schedule a drainage inspection.",
        "confidence": 0.91,
    })
    result = validate_classification(raw)
    assert result["category"] == "flooding"
    assert result["severity"] == "high"
    assert result["department_slug"] == "public_works"
    assert result["confidence"] == pytest.approx(0.91)
    assert "flooding" in result["summary"].lower()


def test_validate_strips_markdown_fences():
    raw = (
        "```json\n"
        '{"category":"pothole","severity":"medium","department_slug":"public_works",'
        '"summary":"A pothole was reported.","recommended_action":"Repair it.","confidence":0.8}'
        "\n```"
    )
    result = validate_classification(raw)
    assert result["category"] == "pothole"
    assert result["confidence"] == pytest.approx(0.8)


def test_validate_rejects_invalid_category():
    raw = json.dumps({
        "category": "alien_invasion",  # not valid
        "severity": "high",
        "department_slug": "public_works",
        "summary": "Something.",
        "recommended_action": "Do something.",
        "confidence": 0.9,
    })
    result = validate_classification(raw)
    assert result == FALLBACK


def test_validate_rejects_invalid_severity():
    raw = json.dumps({
        "category": "pothole",
        "severity": "extreme",  # not valid
        "department_slug": "public_works",
        "summary": "Something.",
        "recommended_action": "Do something.",
        "confidence": 0.9,
    })
    result = validate_classification(raw)
    assert result == FALLBACK


def test_validate_rejects_invalid_dept_slug():
    raw = json.dumps({
        "category": "pothole",
        "severity": "high",
        "department_slug": "magic_department",  # not valid
        "summary": "Something.",
        "recommended_action": "Do something.",
        "confidence": 0.9,
    })
    result = validate_classification(raw)
    assert result == FALLBACK


def test_validate_fallback_on_malformed_json():
    result = validate_classification("This is not JSON at all {{{")
    assert result == FALLBACK


def test_validate_fallback_on_out_of_range_confidence():
    raw = json.dumps({
        "category": "pothole",
        "severity": "high",
        "department_slug": "public_works",
        "summary": "Something.",
        "recommended_action": "Fix it.",
        "confidence": 1.5,  # > 1.0
    })
    result = validate_classification(raw)
    assert result == FALLBACK


def test_validate_fallback_on_empty_summary():
    raw = json.dumps({
        "category": "pothole",
        "severity": "high",
        "department_slug": "public_works",
        "summary": "",  # empty
        "recommended_action": "Fix it.",
        "confidence": 0.8,
    })
    result = validate_classification(raw)
    assert result == FALLBACK


# ─── build_embedding_text — pure function tests ───────────────────────────────


def test_build_embedding_text_includes_description():
    text = build_embedding_text(description="Pothole on Oak Street")
    assert "Pothole on Oak Street" in text


def test_build_embedding_text_includes_all_parts():
    text = build_embedding_text(
        description="Flooding near the park",
        category="flooding",
        severity="high",
        address="123 Park Ave",
        summary="Recurring flooding after rain.",
    )
    assert "Flooding near the park" in text
    assert "flooding" in text
    assert "high" in text
    assert "123 Park Ave" in text
    assert "Recurring flooding" in text


def test_build_embedding_text_skips_none_parts():
    text = build_embedding_text(description="Pothole on Oak St", address=None)
    assert "None" not in text


# ─── classify_report — mocked API call ───────────────────────────────────────


@pytest.mark.asyncio
async def test_classify_report_returns_fallback_without_api_key():
    """Without an API key, classify_report returns FALLBACK immediately."""
    from app.ai.classify import classify_report

    with patch("app.ai.classify.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(openai_api_key="")
        result = await classify_report(description="Big pothole on Main St")
    assert result == FALLBACK


@pytest.mark.asyncio
async def test_classify_report_uses_mocked_openai():
    """classify_report correctly calls AsyncOpenAI and validates the response."""
    from app.ai.classify import classify_report

    valid_json = json.dumps({
        "category": "pothole",
        "severity": "high",
        "department_slug": "public_works",
        "summary": "Large pothole on Main St near the library.",
        "recommended_action": "Dispatch repair crew.",
        "confidence": 0.95,
    })

    mock_choice = MagicMock()
    mock_choice.message.content = valid_json
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("app.ai.classify.get_settings") as mock_settings, \
         patch("app.ai.classify.AsyncOpenAI") as MockClient:
        mock_settings.return_value = MagicMock(openai_api_key="sk-test", ai_model="gpt-4o")
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        MockClient.return_value = mock_instance

        result = await classify_report(description="Big pothole on Main St")

    assert result["category"] == "pothole"
    assert result["severity"] == "high"
    assert result["confidence"] == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_classify_report_falls_back_on_api_error():
    """If OpenAI raises, classify_report returns FALLBACK."""
    from app.ai.classify import classify_report

    with patch("app.ai.classify.get_settings") as mock_settings, \
         patch("app.ai.classify.AsyncOpenAI") as MockClient:
        mock_settings.return_value = MagicMock(openai_api_key="sk-test", ai_model="gpt-4o")
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(side_effect=Exception("Rate limit"))
        MockClient.return_value = mock_instance

        result = await classify_report(description="Broken streetlight")

    assert result == FALLBACK


# ─── Analyze endpoint — validation only ──────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_endpoint_404_for_unknown_report(client: AsyncClient):
    """POST /api/reports/{id}/analyze returns 404 or 503 for unknown reports."""
    import uuid
    # Without DB or with non-existent ID, should not return 200
    res = await client.post(f"/api/reports/{uuid.uuid4()}/analyze")
    assert res.status_code in (404, 503)


# ─── Real API integration (optional) ─────────────────────────────────────────


@pytest.mark.asyncio
@_requires_key
async def test_real_classify_report_returns_valid_output():
    """Call real OpenAI API — only runs when OPENAI_API_KEY is set."""
    from app.ai.classify import classify_report

    result = await classify_report(
        description="There is a large pothole at the intersection of Oak and 5th Ave. "
                    "It is about 30cm across and very deep. Cars have to swerve to avoid it.",
        address="Oak Ave & 5th St",
    )
    from app.ai.classify import VALID_CATEGORIES, VALID_SEVERITIES
    assert result["category"] in VALID_CATEGORIES
    assert result["severity"] in VALID_SEVERITIES
    assert result["confidence"] >= 0.0
    assert result["summary"]
    assert result["recommended_action"]
