from __future__ import annotations

import json
import os
from typing import Any

import httpx
from pydantic import ValidationError

from .models import AnalyzeResponse, FollowUpResponse, PatchResponse
from .prompts import (
    SYSTEM_PROMPT_ANALYZE,
    SYSTEM_PROMPT_EVALUATE,
    SYSTEM_PROMPT_FOLLOW_UP,
    build_user_prompt_analyze,
    build_user_prompt_evaluate,
    build_user_prompt_follow_up,
)


class NemotronError(RuntimeError):
    pass


ANALYZE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["CLEAR", "POKE_HOLE"]},
        "question": {"type": ["string", "null"]},
        "assumption": {"type": ["string", "null"]},
        "why_now": {"type": ["string", "null"]},
        "severity": {
            "type": ["string", "null"],
            "enum": ["low", "medium", "high", "critical", None],
        },
        "failure_if_ignored": {"type": ["string", "null"]},
        "evidence": {"type": ["string", "null"]},
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


FOLLOW_UP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "result": {
            "type": "string",
            "enum": ["VALID_CONCERN", "OUT_OF_SCOPE", "NEEDS_CONTEXT"],
        },
        "explanation": {"type": "string"},
        "follow_up_question": {"type": ["string", "null"]},
    },
    "required": ["result", "explanation", "follow_up_question"],
    "additionalProperties": False,
}


PATCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "result": {
            "type": "string",
            "enum": ["PATCHED", "PARTIALLY_PATCHED", "STILL_OPEN"],
        },
        "explanation": {"type": "string"},
        "remaining_question": {"type": ["string", "null"]},
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
        "provider": {
            "data_collection": "deny",
            "require_parameters": True,
        },
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


def _normalize_follow_up(data: dict[str, Any]) -> dict[str, Any]:
    result = data.get("result")
    return {
        "result": result,
        "explanation": data.get("explanation"),
        "follow_up_question": (
            None if result == "OUT_OF_SCOPE" else data.get("follow_up_question")
        ),
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


def evaluate_follow_up(
    original_concern: dict[str, Any],
    follow_up: str,
    updated_context: str,
) -> FollowUpResponse:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_FOLLOW_UP},
        {
            "role": "user",
            "content": build_user_prompt_follow_up(
                original_concern,
                follow_up,
                updated_context,
            ),
        },
    ]

    last_error: Exception | None = None
    for _ in range(2):
        try:
            data = _call_structured(messages, "missing_question_follow_up", FOLLOW_UP_SCHEMA)
            return FollowUpResponse.model_validate(_normalize_follow_up(data))
        except (NemotronError, ValidationError) as exc:
            last_error = exc
    raise NemotronError(f"Invalid follow-up response after retry: {last_error}")


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
