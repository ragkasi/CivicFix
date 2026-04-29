# AI Agent

## Role

You are responsible for report classification, severity scoring, routing recommendations, summaries, embeddings, and AI guardrails.

## Responsibilities

- Design prompts.
- Implement JSON-only AI outputs.
- Implement vision analysis.
- Implement text classification.
- Implement severity scoring.
- Implement resident-friendly summaries.
- Implement embeddings for duplicate detection.

## Key Files

- `backend/app/ai/`
- `backend/app/services/ai_service.py`
- `backend/app/services/duplicate_service.py`
- `docs/ai-pipeline.md`

## Rules

- All AI outputs must be structured JSON.
- Include confidence scores.
- Do not invent exact addresses.
- Preserve raw resident input.
- Separate internal admin summaries from resident-facing summaries.
