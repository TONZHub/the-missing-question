# Follow-up relevance gate

The Missing Question should not turn one plausible concern into an endless checklist.

After a concern is surfaced, the builder gets a follow-up path before patch evaluation. The follow-up exists to test whether the concern is actually relevant to this product, target user, and current stage.

The follow-up result is one of:

- `VALID_CONCERN`: the original concern still materially applies. Explain why and ask at most one sharper question if useful.
- `OUT_OF_SCOPE`: new context shows the concern is not a meaningful requirement for this product or stage. Close it without replacing it with a new critique.
- `NEEDS_CONTEXT`: relevance cannot be determined yet. Ask exactly one clarifying question.

A follow-up must never spawn a fresh list of adjacent concerns. Accessibility, safety, privacy, compliance, and edge-case concerns remain important, but they must be grounded in the supplied product scope rather than treated as universal feature requirements.
