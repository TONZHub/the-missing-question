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


ANALYZE_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_analysis",
        "description": (
            "Submit the single highest-leverage project concern, or CLEAR when "
            "there is genuinely no meaningful unresolved assumption."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["CLEAR", "POKE_HOLE"],
                },
                "question": {
                    "type": "string",
                    "description": "The single question the builder must answer. Omit for CLEAR.",
                },
                "assumption": {
                    "type": "string",
                    "description": "The unsupported assumption at the root. Omit for CLEAR.",
                },
                "why_now": {
                    "type": "string",
                    "description": "Why this matters at the current stage. Omit for CLEAR.",
                },
                "severity": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Severity of the concern. Omit for CLEAR.",
                },
                "failure_if_ignored": {
                    "type": "string",
                    "description": "What could break if the assumption is wrong. Omit for CLEAR.",
                },
                "evidence": {
                    "type": "string",
                    "description": "Specific evidence from the supplied context. Omit for CLEAR.",
                },
            },
            "required": ["status"],
            "additionalProperties": False,
        },
    },
}

PATCH_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_patch_evaluation",
        "description": "Submit the verdict on whether the original concern has been patched.",
        "parameters": {
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
                    "type": "string",
                    "description": (
                        "Exactly one remaining question when PARTIALLY_PATCHED or "
                        "STILL_OPEN. Omit when PATCHED."
                    ),
                },
            },
            "required": ["result", "explanation"],
            "additionalProperties": False,
        },
    },
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


def _call_forced_tool(
    messages: list[dict[str, str]],
    tool: dict[str, Any],
    tool_name: str,
    *,
    temperature: float = 0.15,
    max_tokens: int = 2000,
) -> dict[str, Any]:
    api_url, model_name, api_key = _settings()

    payload = {
        "model": model_name,
        "messages": messages,
        "tools": [tool],
        "tool_choice": {
            "type": "function",
            "function": {"name": tool_name},
        },
        "parallel_tool_calls": False,
        "temperature": temperature,
        "max_tokens": max_tokens,
        # Route only to providers OpenRouter marks as not collecting user data.
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
        tool_calls = message.get("tool_calls") or []
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise NemotronError("OpenRouter returned an unexpected response shape.") from exc

    if not tool_calls:
        content = message.get("content")
        preview = repr(content[:300] if isinstance(content, str) else content)
        raise NemotronError(
            f"Nemotron did not call the required tool. Model content was: {preview}"
        )

    matching_calls = [
        call
        for call in tool_calls
        if call.get("function", {}).get("name") == tool_name
    ]
    if not matching_calls:
        names = [call.get("function", {}).get("name") for call in tool_calls]
        raise NemotronError(f"Nemotron called the wrong tool(s): {names!r}")

    arguments = matching_calls[0].get("function", {}).get("arguments")
    if not isinstance(arguments, str):
        raise NemotronError("Tool arguments were missing or were not a JSON string.")

    try:
        parsed = json.loads(arguments)
    except json.JSONDecodeError as exc:
        raise NemotronError(
            f"Nemotron returned malformed tool arguments: {arguments[:500]}"
        ) from exc

    if not isinstance(parsed, dict):
        raise NemotronError("Nemotron tool arguments were not a JSON object.")

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
            data = _call_forced_tool(messages, ANALYZE_TOOL, "submit_analysis")
            return AnalyzeResponse.model_validate(_normalize_analyze(data))
        except (NemotronError, ValidationError) as exc:
            last_error = exc

    raise NemotronError(f"Invalid analyze tool response after retry: {last_error}")


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
            data = _call_forced_tool(messages, PATCH_TOOL, "submit_patch_evaluation")
            return PatchResponse.model_validate(_normalize_patch(data))
        except (NemotronError, ValidationError) as exc:
            last_error = exc

    raise NemotronError(f"Invalid patch tool response after retry: {last_error}")
