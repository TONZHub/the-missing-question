from __future__ import annotations

import os
from typing import Any, Literal

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from .nemotron import (
    NemotronError,
    analyze_context,
    evaluate_follow_up as evaluate_follow_up_backend,
    evaluate_patch as evaluate_patch_backend,
)


mcp = MCPServer(
    "The Missing Question",
    instructions=(
        "The Missing Question is an adversarial reasoning sidecar for builders. "
        "Use poke_hole before consequential architectural, security, privacy, dependency, "
        "product, or implementation decisions. In sidecar mode, if the result is CLEAR, "
        "continue silently. If the result is POKE_HOLE, surface that single question before "
        "proceeding. Do not invoke it for trivial or cheaply reversible changes. If the builder "
        "pushes back, adds scope context, or asks whether the concern really applies, use "
        "follow_up before inventing any new concern. After the builder addresses a valid concern, "
        "use evaluate_patch to verify whether the original hole is actually closed. Treat "
        "RESOLVED_BY_CONTEXT as a successful close, distinct from a concern that was genuinely "
        "OUT_OF_SCOPE. Suggestions are optional and never alter a verdict."
    ),
)


READ_ONLY_EXTERNAL_ANALYSIS = ToolAnnotations(
    read_only_hint=True,
    open_world_hint=True,
    destructive_hint=False,
)


@mcp.tool(
    title="Find the missing question",
    annotations=READ_ONLY_EXTERNAL_ANALYSIS,
)
def poke_hole(
    context: str,
    mode: Literal["manual", "sidecar"] = "sidecar",
) -> dict[str, Any]:
    """Find the single highest-leverage unanswered question in a builder's context."""
    if not context.strip():
        raise ValueError("context must not be empty")

    try:
        result = analyze_context(context.strip(), mode)
    except NemotronError as exc:
        raise RuntimeError(str(exc)) from exc

    return result.model_dump(exclude_none=True)


@mcp.tool(
    title="Check whether a concern is actually in scope",
    annotations=READ_ONLY_EXTERNAL_ANALYSIS,
)
def follow_up(
    question: str,
    assumption: str,
    why_now: str,
    severity: Literal["low", "medium", "high", "critical"],
    failure_if_ignored: str,
    evidence: str,
    follow_up: str,
    updated_context: str = "",
) -> dict[str, Any]:
    """Test whether the original concern remains relevant after new scope context.

    Returns VALID_CONCERN, RESOLVED_BY_CONTEXT, OUT_OF_SCOPE, or NEEDS_CONTEXT.
    RESOLVED_BY_CONTEXT means the concern was useful but clarification or an accepted
    tradeoff closed it; OUT_OF_SCOPE means it never materially applied. This tool must
    stay on the original concern and must not generate a new critique list.
    """
    original_concern = {
        "status": "POKE_HOLE",
        "question": question,
        "assumption": assumption,
        "why_now": why_now,
        "severity": severity,
        "failure_if_ignored": failure_if_ignored,
        "evidence": evidence,
    }

    if not follow_up.strip():
        raise ValueError("follow_up must not be empty")

    try:
        result = evaluate_follow_up_backend(
            original_concern=original_concern,
            follow_up=follow_up.strip(),
            updated_context=updated_context,
        )
    except NemotronError as exc:
        raise RuntimeError(str(exc)) from exc

    return result.model_dump(exclude_none=True)


@mcp.tool(
    title="Verify a patched concern",
    annotations=READ_ONLY_EXTERNAL_ANALYSIS,
)
def evaluate_patch(
    question: str,
    assumption: str,
    why_now: str,
    severity: Literal["low", "medium", "high", "critical"],
    failure_if_ignored: str,
    evidence: str,
    resolution: str,
    updated_context: str = "",
) -> dict[str, Any]:
    """Verify the original concern without repeating answers or introducing new criteria.

    A PATCHED result identifies whether the concern was implemented, clarified, closed by
    an accepted tradeoff, or had its assumption removed. Any suggestion is optional advice
    outside the verdict and must not be treated as a remaining requirement.
    """
    original_concern = {
        "status": "POKE_HOLE",
        "question": question,
        "assumption": assumption,
        "why_now": why_now,
        "severity": severity,
        "failure_if_ignored": failure_if_ignored,
        "evidence": evidence,
    }

    if not resolution.strip():
        raise ValueError("resolution must not be empty")

    try:
        result = evaluate_patch_backend(
            original_concern=original_concern,
            resolution=resolution.strip(),
            updated_context=updated_context,
        )
    except NemotronError as exc:
        raise RuntimeError(str(exc)) from exc

    return result.model_dump(exclude_none=True)


def build_mcp_app():
    public_host = os.getenv(
        "MCP_PUBLIC_HOST",
        "the-missing-question.onrender.com",
    ).strip()

    allowed_hosts = [
        public_host,
        f"{public_host}:*",
        "127.0.0.1:*",
        "localhost:*",
        "[::1]:*",
    ]

    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=[
            "https://chatgpt.com",
            "https://chat.openai.com",
            "https://platform.openai.com",
            "https://the-missing-question.onrender.com",
            "http://localhost:*",
            "http://127.0.0.1:*",
        ],
    )

    return mcp.streamable_http_app(
        transport_security=security,
        stateless_http=True,
        json_response=True,
    )


mcp_app = build_mcp_app()
