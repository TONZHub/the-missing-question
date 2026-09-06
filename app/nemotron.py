from __future__ import annotations

import json
import os
from typing import Any

import httpx
from pydantic import ValidationError

from .models import AnalyzeResponse, PatchResponse
from .prompts import (
    SYSTEM_PROMPT_ANALYZE,
    SYSTEM_PROMPT_EVALUATE,
    build_user_prompt_analyze,
    build_user_prompt_evaluate,
)


class NemotronError(RuntimeError):
    pass


ANALYZE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["CLEAR", "POKE_HOLE"],
        },
        "question": {
            "type": ["string", "null"],
            "description": "The single question the builder must answer. Null for CLEAR.",
        },
        "assumption": {
            "type": ["string", "null"],
            "description": "The unsupported assumption at the root. Null for CLEAR.",
        },
        "why_now": {
            "type": ["string", "null"],
            "description": "Why this matters at the current stage. Null for CLEAR.",
        },
        "severity": {
            "type": ["string", "null"],
            "enum": ["low", "medium", "high", "critical", None],
            "description": "Severity of the concern. Null for CLEAR.",
        },
        "failure_if_ignored": {
            "type": ["string", "null"],
            "description": "What could break if the assumption is wrong. Null for CLEAR.",
        },
        "evidence": {
            "type": ["string", "null"],
            "description": "Specific evidence from the supplied context. Null for CLEAR.",
        },
    },
    "required": [
        "status",
        "question",
        "assumption",
        "why_now",
        "severity",
        "failure_if_ignored",
        "evidence",
    ],
    "additionalProperties": False,
}


PATCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "result": {
            "type": "string",
            "enum": ["PATCHED", "PARTIALLY_PATCHED", "STILL_OPEN"],
        },
        "explanation": {
            "type": "string",
            "description": "A brief justification for the verdict.",
        },
        "remaining_question": {
            "type": ["string", "null"],
            "description": (
                "Exactly one remaining question when PARTIALLY_PATCHED or STILL_OPEN. "
                "Null when PATCHED."
            ),
        },
    },
    "required": ["result", "explanation", "remaining_question"],
    "additionalProperties": False,
}


def _env(var: str, default: str | None = None) -> str:
    value = os.getenv(var, default)
    if value is None or not value.strip():
        raise NemotronError(f"Environment variable {var} is not set.")
    return value.strip()


def _settings() -> tuple[str, str, str]:
    return (
        _env("NEMOTRON_API_URL"),
        _env("NEMOTRON_MODEL_NAME"),
        _env("NEMOTRON_API_KEY"),
    )


def _extract_text_content(message: dict[str, Any]) -> str:
    content = message.get("content")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        if parts:
            return "".join(parts)

    raise NemotronError("OpenRouter response did not contain structured text content.")


def _call_structured(
    messages: list[dict[str, str]],
    schema_name: str,
    schema: dict[str, Any],
    *,
    temperature: float = 0.15,
    max_tokens: int = 2000,
) -> dict[str, Any]:
    api_url, model_name, api_key = _settings()

    payload = {
        "model": model_name,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        },
        "temperature": temperature,
        "max_tokens": max_tokens,
        # Route only to providers OpenRouter marks as not collecting user data,
        # and only to providers that support the parameters in this request.
        "provider": {
            "data_collection": "deny",
            "require_parameters": True,
        },
        # Let Nemotron reason, but don't return the reasoning trace.
        "reasoning": {"exclude": True},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv(
            "OPENROUTER_SITE_URL",
            "https://the-missing-question.onrender.com",
        ),
        "X-Title": "The Missing Question",
    }

    try:
        response = httpx.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=httpx.Timeout(60.0),
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:1000]
        raise NemotronError(
            f"Nemotron API returned HTTP {exc.response.status_code}: {detail}"
        ) from exc
    except httpx.HTTPError as exc:
        raise NemotronError(f"Nemotron API request failed: {exc}") from exc

    try:
        data = response.json()
        message = data["choices"][0]["message"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise NemotronError("OpenRouter returned an unexpected response shape.") from exc

    raw = _extract_text_content(message)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NemotronError(
            f"Nemotron returned malformed structured JSON: {raw[:500]}"
        ) from exc

    if not isinstance(parsed, dict):
        raise NemotronError("Nemotron structured output was not a JSON object.")

    return parsed


def _normalize_analyze(data: dict[str, Any]) -> dict[str, Any]:
    status = data.get("status")

    if status == "CLEAR":
        return {
            "status": "CLEAR",
            "question": None,
            "assumption": None,
            "why_now": None,
            "severity": None,
            "failure_if_ignored": None,
            "evidence": None,
        }

    return {
        "status": status,
        "question": data.get("question"),
        "assumption": data.get("assumption"),
        "why_now": data.get("why_now"),
        "severity": data.get("severity"),
        "failure_if_ignored": data.get("failure_if_ignored"),
        "evidence": data.get("evidence"),
    }


def _normalize_patch(data: dict[str, Any]) -> dict[str, Any]:
    result = data.get("result")
    return {
        "result": result,
        "explanation": data.get("explanation"),
        "remaining_question": None if result == "PATCHED" else data.get("remaining_question"),
    }


def analyze_context(context: str, mode: str = "manual") -> AnalyzeResponse:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ANALYZE},
        {"role": "user", "content": build_user_prompt_analyze(context, mode)},
    ]

    last_error: Exception | None = None

    for _ in range(2):
        try:
            data = _call_structured(messages, "missing_question_analysis", ANALYZE_SCHEMA)
            return AnalyzeResponse.model_validate(_normalize_analyze(data))
        except (NemotronError, ValidationError) as exc:
            last_error = exc

    raise NemotronError(f"Invalid analyze response after retry: {last_error}")


def evaluate_patch(
    original_concern: dict[str, Any],
    resolution: str,
    updated_context: str,
) -> PatchResponse:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_EVALUATE},
        {
            "role": "user",
            "content": build_user_prompt_evaluate(
                original_concern,
                resolution,
                updated_context,
            ),
        },
    ]

    last_error: Exception | None = None

    for _ in range(2):
        try:
            data = _call_structured(messages, "missing_question_patch", PATCH_SCHEMA)
            return PatchResponse.model_validate(_normalize_patch(data))
        except (NemotronError, ValidationError) as exc:
            last_error = exc

    raise NemotronError(f"Invalid patch response after retry: {last_error}")
