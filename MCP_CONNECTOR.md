# The Missing Question — MCP connector

The existing web app and REST API stay intact. This branch adds a remote Streamable HTTP MCP endpoint at:

```text
https://the-missing-question.onrender.com/mcp
```

## Tools

### `poke_hole`

Finds the single highest-leverage unanswered question in project context.

Inputs:

- `context`: project idea, architecture, PRD, diff, decision, etc.
- `mode`: `sidecar` (default) or `manual`

Use `sidecar` for automatic coding-agent integrations. In this mode the connector should remain quiet unless the concern is high-confidence and high-impact.

Typical output:

```json
{
  "status": "POKE_HOLE",
  "question": "What happens if the permission this workflow depends on is denied?",
  "assumption": "The required permission will be available.",
  "why_now": "Several downstream features are about to depend on it.",
  "severity": "high",
  "failure_if_ignored": "The core workflow could become unusable after substantial implementation work.",
  "evidence": "Account linking is foundational to the proposed workflow."
}
```

When no interruption is warranted:

```json
{"status":"CLEAR"}
```

### `follow_up`

Re-checks only the original concern after the builder supplies scope or architecture context.
It distinguishes `OUT_OF_SCOPE` (the concern never materially applied) from
`RESOLVED_BY_CONTEXT` (the concern was legitimate, but clarification, a recovery path,
or an accepted tradeoff closed it). It must not repeat an answered question.

### `evaluate_patch`

Checks whether a builder's proposed resolution actually closes a previously surfaced concern.

Pass the fields from the earlier `POKE_HOLE` result plus:

- `resolution`
- `updated_context` (optional)

It returns one of:

- `PATCHED`
- `PARTIALLY_PATCHED`
- `STILL_OPEN`

A `PATCHED` response includes `resolution_basis`: `IMPLEMENTED`, `CLARIFIED`,
`ACCEPTED_TRADEOFF`, or `ASSUMPTION_REMOVED`. An optional `suggestion` is outside
the verdict and never becomes a remaining requirement.

## Agent behavior

Recommended host-agent instruction:

> Use The Missing Question before consequential architectural decisions, new external dependencies, privacy/security choices, expensive implementation paths, or changes that create substantial downstream reliance on an unverified assumption. Call `poke_hole` with `mode="sidecar"`. If it returns `CLEAR`, continue silently. If it returns `POKE_HOLE`, surface the single question before proceeding. Do not invoke it for trivial or cheaply reversible changes. Use `follow_up` for new relevance context and preserve the distinction between `OUT_OF_SCOPE` and `RESOLVED_BY_CONTEXT`. After the builder addresses a concern, call `evaluate_patch` to verify whether the hole is actually patched. Never treat `suggestion` as part of the verdict.

## Render

No new required secret is needed for the MCP connector. The existing Nemotron/OpenRouter variables are reused.

Optional environment variable:

```text
MCP_PUBLIC_HOST=the-missing-question.onrender.com
```

Only change this if the public hostname changes (for example, when moving to a custom domain).

## Security note

The MCP endpoint is currently unauthenticated, just like the public prototype's REST analysis endpoints. That is appropriate for a hackathon demo, but add authentication/rate limiting before treating it as a production connector for private project context.
