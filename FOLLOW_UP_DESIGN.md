# Follow-up relevance gate

The Missing Question should not turn one plausible concern into an endless checklist.

After a concern is surfaced, the builder gets a follow-up path before patch evaluation. The follow-up exists to test whether the concern is actually relevant to this product, target user, and current stage.

The follow-up result is one of:

- `VALID_CONCERN`: the original concern still materially applies. Explain why and ask at most one sharper question if useful.
- `RESOLVED_BY_CONTEXT`: the concern was relevant and useful, but the new context closes it through clarification, a recovery path, a removed assumption, or an explicit acceptable tradeoff.
- `OUT_OF_SCOPE`: new context shows the concern is not a meaningful requirement for this product or stage. Close it without replacing it with a new critique.
- `NEEDS_CONTEXT`: relevance cannot be determined yet. Ask exactly one clarifying question.

A follow-up must never spawn a fresh list of adjacent concerns. Accessibility, safety, privacy, compliance, and edge-case concerns remain important, but they must be grounded in the supplied product scope rather than treated as universal feature requirements.

`OUT_OF_SCOPE` must not become a wastebasket for answered concerns. For example, a local-only app that loses local state on uninstall but explicitly re-pairs and rescans Gmail has answered a legitimate recoverability question. That is `RESOLVED_BY_CONTEXT`, with re-onboarding friction named as an accepted tradeoff; it is not evidence that the concern never mattered.
