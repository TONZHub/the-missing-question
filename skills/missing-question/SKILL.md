---
name: missing-question
description: Use The Missing Question MCP sidecar to challenge high-leverage assumptions before consequential project decisions, test whether concerns are actually in scope, and verify whether valid concerns were patched.
---

# The Missing Question

Use this skill as a selective adversarial checkpoint, not as a constant critic.

## When to call `poke_hole`

Call `poke_hole` with `mode="sidecar"` before a decision that would create meaningful downstream dependence on an unverified assumption, especially:

- consequential architecture choices;
- new external APIs, services, permissions, or dependencies;
- security, privacy, safety, or consent decisions;
- expensive or difficult-to-reverse implementation paths;
- product assumptions that could invalidate substantial future work;
- decisions where discovering the flaw later would force a major redesign.

Do not call it for trivial edits, routine refactors, formatting, cheaply reversible implementation details, or every ordinary coding step.

## How to handle the result

If `poke_hole` returns `CLEAR`, continue silently. Do not announce that a check occurred unless the user asks.

If it returns `POKE_HOLE`, stop before committing to the dependent decision and surface the single returned question. Preserve the returned assumption, why-now rationale, severity, failure mode, and evidence so they can be passed to `follow_up` or `evaluate_patch` later.

Do not add a second critique of your own. The value of this tool is one high-leverage interruption, not a list of generic concerns.

The blocking question must test exactly one failure mode. Do not append optional improvements, extra modalities, roadmap ideas, best practices, or feature suggestions to the same question. If an adjacent idea would not change whether the core concern is valid, it is not part of the blocking question.

## Follow-up relevance loop

If the builder pushes back, adds scope context, says a concern does not apply, or asks why it matters, call `follow_up` on the ORIGINAL concern before generating anything new.

- `VALID_CONCERN`: explain why the original concern still applies. Surface at most the one returned sharper question.
- `RESOLVED_BY_CONTEXT`: close the concern and continue. Say that the concern was useful, then briefly name the clarification, recovery path, removed assumption, or accepted tradeoff that resolved it.
- `OUT_OF_SCOPE`: drop the concern and continue. Do not replace it with another critique.
- `NEEDS_CONTEXT`: ask exactly the one returned clarifying question.

Do not turn one concern into a checklist of adjacent accessibility, safety, privacy, compliance, or edge-case requirements. These concerns matter only when grounded in the product scope, intended users, current stage, or a concrete obligation.

Do not collapse `RESOLVED_BY_CONTEXT` into `OUT_OF_SCOPE`. The first means the question earned its keep and received a satisfactory answer; the second means it never materially belonged. Neither result permits another question about the same answered point.

Any follow-up question must stay inside the original failure mode. Optional suggestions do not belong in `follow_up_question`.

## Patch loop

After the builder explains how they addressed a valid concern, call `evaluate_patch` using the original concern fields plus the builder's resolution and any updated context.

- `PATCHED`: continue with the work.
- `PARTIALLY_PATCHED`: surface the one remaining question and wait for a real resolution before relying on the assumption.
- `STILL_OPEN`: explain that the original risk remains and do not treat reassurance or rewording as a patch.

A patch may remove the original assumption entirely rather than proving it. That still counts as patched when the original failure mode no longer applies.

Use `resolution_basis` when explaining PATCHED: `IMPLEMENTED`, `CLARIFIED`, `ACCEPTED_TRADEOFF`, or `ASSUMPTION_REMOVED`. Do not translate a clarification or accepted tradeoff into “the concern was irrelevant.”

If `evaluate_patch` also returns a `suggestion`, label it “May I suggest” and treat it as optional and non-blocking. It may improve the product, but it is not part of the original acceptance criterion, must not be repeated as a remaining question, and must not prevent progress after a `PATCHED` verdict.

The question/suggestion boundary is strict: `remaining_question` contains only information necessary to resolve the original failure mode. `suggestion` contains only optional adjacent improvements. Never repeat the same idea in both. If removing a clause from the question would not change the verdict, move that clause to “May I suggest.”

## Manual scrutiny

When the user explicitly asks to "poke holes", "stress-test this", "find the missing question", or otherwise requests critique, call `poke_hole` with `mode="manual"`. Manual mode should actively search for the strongest legitimate unresolved assumption without inventing one.

## Tone

Keep the interruption concise. The connector is a checkpoint, not a lecture. Let The Missing Question provide the adversarial framing; the host agent should remain useful and continue immediately once a concern is dismissed as out of scope or genuinely patched.
