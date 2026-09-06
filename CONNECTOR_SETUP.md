# The Missing Question — Connector setup

The remote MCP endpoint is:

```text
https://the-missing-question.onrender.com/mcp
```

## Fastest Codex test

Add the remote server directly:

```bash
codex mcp add missing-question --url https://the-missing-question.onrender.com/mcp
```

Confirm it is configured:

```bash
codex mcp list
```

Codex stores MCP configuration in `~/.codex/config.toml` by default. The Codex CLI, IDE extension, and supported desktop surfaces share this configuration.

A manual config entry is equivalent to:

```toml
[mcp_servers.missing-question]
url = "https://the-missing-question.onrender.com/mcp"
```

The hackathon prototype is currently unauthenticated, so no bearer token or OAuth login is required.

## Tools

### `poke_hole`

Inputs:

- `context`: product idea, architecture, PRD, diff, implementation plan, or decision context.
- `mode`: `sidecar` by default; use `manual` when the user explicitly asks for scrutiny.

In sidecar mode, `CLEAR` means continue silently. `POKE_HOLE` means surface the single concern before creating further downstream dependence on the assumption.

### `evaluate_patch`

Pass the original concern fields plus the builder's resolution and optional updated context. Returns `PATCHED`, `PARTIALLY_PATCHED`, or `STILL_OPEN`.

## Plugin package

This repository also packages the connector as an OpenAI plugin:

```text
.codex-plugin/plugin.json
.mcp.json
skills/missing-question/SKILL.md
```

The bundled skill teaches the host agent when to invoke the MCP sidecar automatically, when to remain silent, and how to complete the patch loop.

## Security before production

The public prototype accepts project context without authentication. Before using it for confidential code or private product context, add authentication, rate limiting, abuse controls, and an explicit data-retention policy.
