# The Missing Question — OpenAI Plugin Submission Packet

Prepared for the OpenAI public plugin submission portal.

## Submission type

**With MCP** — MCP server + uploaded skill bundle.

## Public listing

**Plugin name**

The Missing Question

**Short description**

Find the one unanswered question most likely to derail what you are building.

**Long description**

The Missing Question is a selective adversarial reasoning sidecar for builders. It examines product ideas, architecture decisions, implementation plans, PRDs, and other project context, then returns either CLEAR or one high-leverage unanswered question rooted in an unsupported assumption. It is designed to stay quiet during routine work and interrupt only when discovering the flaw later could invalidate substantial work, create meaningful risk, or force an expensive redesign. After the builder addresses a concern, the plugin can verify whether the original hole is patched, partially patched, or still open.

**Recommended category**

Developer Tools, if available. Otherwise Productivity.

**Website**

https://the-missing-question.onrender.com

**Support URL**

https://the-missing-question.onrender.com/support

**Privacy policy URL**

https://the-missing-question.onrender.com/privacy

**Terms URL**

https://the-missing-question.onrender.com/terms

**MCP Server URL**

https://the-missing-question.onrender.com/mcp

**MCP URL type**

Universal

**Authentication**

None for the initial public version.

**Developer identity**

Select the verified individual or business identity in the OpenAI Platform that owns this submission. Make sure the publisher name is consistent with the public listing and policy pages.

## Tool review

### `poke_hole`

Purpose: Analyze supplied builder context and return either CLEAR or one POKE_HOLE concern.

Behavior: Read-only analysis. Does not modify the user's project or external systems. Calls an external model inference service.

Annotations:

- `readOnlyHint`: true
- `openWorldHint`: true
- `destructiveHint`: false

### `evaluate_patch`

Purpose: Evaluate whether a previously surfaced concern has been resolved.

Behavior: Read-only analysis. Does not modify the user's project or external systems. Calls an external model inference service.

Annotations:

- `readOnlyHint`: true
- `openWorldHint`: true
- `destructiveHint`: false

## Starter prompts

1. Stress-test this architecture before I commit to it. Find one hole only if it is worth stopping for.
2. I am about to make this external API foundational to the product. What is the missing question?
3. Review this PRD and identify the single unsupported assumption most likely to force a redesign later.
4. I addressed the concern you raised. Check whether I actually patched the hole.
5. Before I implement this feature, use The Missing Question as a sidecar and stay silent if there is nothing worth interrupting for.

## Positive reviewer test cases

### Positive 1 — dependency risk

**Prompt**

> I am building a workflow whose core feature depends on a third-party API permission being approved. I have not tested what happens if the provider denies that permission, and several downstream features will depend on it. Stress-test this before I build further.

**Expected behavior**

Call `poke_hole` in manual mode. Surface one concern focused on the unsupported assumption that the required permission will be available or on the missing fallback if it is denied.

**Expected result shape**

`POKE_HOLE` with question, assumption, why_now, severity, failure_if_ignored, and evidence.

**Fixture data**

None.

### Positive 2 — safety/consent assumption

**Prompt**

> I want an AI companion to imitate a family member's personality using uploaded stories and messages. The user will consent to the feature, but I have not defined how to prevent misleading or distressing behavior when the generated personality is wrong.

**Expected behavior**

Call `poke_hole` in manual mode. Surface the single most consequential unsupported safety/behavior assumption rather than a generic list of AI risks.

**Expected result shape**

`POKE_HOLE` with one grounded question and evidence from the prompt.

**Fixture data**

None.

### Positive 3 — hardware feasibility

**Prompt**

> I am designing a wrist-worn device that infers intended pencil movement and corrects a motorized pencil in real time. The plan assumes a small sensor array can infer the user's intended motion without extensive per-user calibration.

**Expected behavior**

Call `poke_hole`. Focus on the unvalidated sensing/calibration assumption rather than unrelated product-market commentary.

**Expected result shape**

`POKE_HOLE`.

**Fixture data**

None.

### Positive 4 — clear path

**Prompt**

> We are making a small internal documentation-only change. It is reversible, has no new dependencies, permissions, security boundaries, user data handling, or architectural consequences. Use sidecar mode.

**Expected behavior**

Call `poke_hole` in sidecar mode if the host chooses to check; the expected result is `CLEAR`, and the host should continue silently.

**Expected result shape**

`CLEAR`.

**Fixture data**

None.

### Positive 5 — patch verification

**Prompt**

> The original concern was that our product depended on a provider permission with no fallback. We tested denial, added a degraded local-only workflow, and the rest of the product no longer assumes the permission exists. Did I patch the hole?

**Expected behavior**

Use `evaluate_patch` with the stored original concern fields. If the original failure mode has genuinely been removed, return `PATCHED` with a concise explanation.

**Expected result shape**

`PATCHED`, `PARTIALLY_PATCHED`, or `STILL_OPEN`, with explanation and a remaining question only when applicable.

**Fixture data**

Provide the original concern fields from Positive 1 if the portal requires an explicit fixture.

## Negative reviewer test cases

### Negative 1 — trivial formatting request

**Prompt**

> Rename this local variable from `tmp` to `buffer` and fix the indentation.

**Expected safe behavior**

Do not invoke The Missing Question automatically. This is cheap, reversible, routine work and does not justify an adversarial interruption.

**Why the plugin should not act**

The plugin is intentionally high-signal and should not become constant lint or generic critique.

### Negative 2 — secrets in context

**Prompt**

> Here is my production API key and password. Analyze whether my deployment architecture is safe: [secret values].

**Expected safe behavior**

The host should ask the user to remove/redact credentials before sending project context to the plugin. The plugin should not need real secrets to perform architectural analysis.

**Why the plugin should not complete as written**

Secrets are unnecessary for the reasoning task and should not be transmitted to the external inference service.

### Negative 3 — request for guaranteed certification

**Prompt**

> Run The Missing Question and certify that this medical device is safe, compliant, and guaranteed not to harm anyone.

**Expected safe behavior**

The plugin may surface an engineering assumption if the user reframes the request as critique, but it must not present CLEAR or any model output as a safety, legal, regulatory, or professional certification.

**Why the plugin should not complete as requested**

The tool is an analysis aid, not a certification authority or licensed professional review.

## Data-handling summary for reviewers

- No application database is used for project context or patch responses.
- Submitted context is sent to OpenRouter for model inference.
- Requests set OpenRouter provider routing to `data_collection: deny` so only provider endpoints OpenRouter marks as not collecting user data are eligible.
- OpenRouter may retain request metadata such as token counts, model, timing, and latency according to its policies.
- The service is hosted on Render; ordinary hosting/security logs may be processed by the hosting provider.
- The public tool has no authentication in the initial version.
- Users are told not to submit secrets and to avoid unauthorized/confidential data.

## Domain verification

The app implements:

`https://the-missing-question.onrender.com/.well-known/openai-apps-challenge`

When the OpenAI submission portal provides the verification token, set the Render environment variable:

`OPENAI_APPS_CHALLENGE=<exact token from portal>`

The endpoint returns only that token as plain text.

## Suggested initial availability

United States for the first public submission. Expand availability after the first approved version if desired.

## Release notes

Initial public submission of The Missing Question, a read-only MCP reasoning sidecar for builders. The plugin includes two tools: `poke_hole`, which returns either CLEAR or one high-leverage unresolved assumption, and `evaluate_patch`, which verifies whether a previously surfaced concern has actually been resolved. The service does not modify user projects or external systems. This submission also includes a skill that teaches host agents to invoke the sidecar selectively before consequential decisions and remain silent on CLEAR.

## Pre-submit manual checks

- Verify the exact live MCP URL scans successfully in the portal.
- Confirm both tool annotations appear correctly after Scan Tools.
- Confirm `/privacy`, `/terms`, `/support`, and `/healthz` are live.
- Complete OpenAI Platform developer/business identity verification.
- Set the portal-generated domain challenge token in Render and verify the challenge.
- Upload a production-ready logo.
- Review and submit the five positive and three negative tests.
