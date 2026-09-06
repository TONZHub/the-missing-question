from __future__ import annotations

import os
from typing import Any, Literal

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .nemotron import NemotronError, analyze_context, evaluate_patch as evaluate_patch_backend


mcp = MCPServer(
    "The Missing Question",
    instructions=(
        "The Missing Question is an adversarial reasoning sidecar for builders. "
        "Use poke_hole before consequential architectural, security, privacy, dependency, "
        "product, or implementation decisions. In sidecar mode, if the result is CLEAR, "
        "continue silently. If the result is POKE_HOLE, surface that single question before "
        "proceeding. Do not invoke it for trivial or cheaply reversible changes. After the "
        "builder addresses a concern, use evaluate_patch to verify whether the original hole "
        "is actually closed."
    ),
)


@mcp.tool()
def poke_hole(
    context: str,
    mode: Literal["manual", "sidecar"] = "sidecar",
) -> dict[str, Any]:
    """Find the single highest-leverage unanswered question in a builder's context.

    Use mode='sidecar' for automatic agent integrations: interrupt only for
    high-confidence, high-impact concerns. Use mode='manual' when the builder
    explicitly asks for scrutiny.
    """
    if not context.strip():
        raise ValueError("context must not be empty")

    try:
        result = analyze_context(context.strip(), mode)
    except NemotronError as exc:
        raise RuntimeError(str(exc)) from exc

    return result.model_dump(exclude_none=True)


@mcp.tool()
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
    """Verify whether a builder actually patched a previously surfaced concern.

    Pass the fields from the earlier POKE_HOLE result plus the builder's proposed
    resolution. Returns PATCHED, PARTIALLY_PATCHED, or STILL_OPEN.
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
    """Build the Streamable HTTP MCP application for mounting under FastAPI."""
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
