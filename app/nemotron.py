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
    SYSTEM_PROMPT_REPAIR,
    build_user_prompt_analyze,
    build_user_prompt_evaluate,
)


class NemotronError(RuntimeError):
    pass


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


def _call_llm(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.15,
    max_tokens: int = 700,
) -> str:
    api_url, model_name, api_key = _settings()

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=httpx.Timeout(45.0),
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise NemotronError(f"Nemotron API request failed: {exc}") from exc

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise NemotronError("Nemotron API returned an unexpected response shape.") from exc


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()

    try:
        value = json.loads(cleaned)
        if not isinstance(value, dict):
            raise NemotronError("Model returned JSON that was not an object.")
        return value
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise NemotronError("Model did not return valid JSON.")

        try:
            value = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise NemotronError("Model returned malformed JSON.") from exc

        if not isinstance(value, dict):
            raise NemotronError("Model returned JSON that was not an object.")
        return value


def _repair_once(
    original_messages: list[dict[str, str]],
    bad_output: str,
) -> dict[str, Any]:
    repair_messages = [
        *original_messages,
        {"role": "assistant", "content": bad_output},
        {"role": "system", "content": SYSTEM_PROMPT_REPAIR},
    ]
    repaired = _call_llm(repair_messages, temperature=0.0)
    return _extract_json(repaired)


def analyze_context(context: str, mode: str = "manual") -> AnalyzeResponse:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_ANALYZE},
        {"role": "user", "content": build_user_prompt_analyze(context, mode)},
    ]

    raw = _call_llm(messages)

    for attempt in range(2):
        try:
            data = _extract_json(raw) if attempt == 0 else _repair_once(messages, raw)
            return AnalyzeResponse.model_validate(data)
        except (NemotronError, ValidationError) as exc:
            if attempt == 1:
                raise NemotronError(f"Invalid analyze response after repair: {exc}") from exc

    raise NemotronError("Unable to validate analyze response.")


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

    raw = _call_llm(messages)

    for attempt in range(2):
        try:
            data = _extract_json(raw) if attempt == 0 else _repair_once(messages, raw)
            return PatchResponse.model_validate(data)
        except (NemotronError, ValidationError) as exc:
            if attempt == 1:
                raise NemotronError(f"Invalid patch response after repair: {exc}") from exc

    raise NemotronError("Unable to validate patch response.")
