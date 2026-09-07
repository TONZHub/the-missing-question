from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.models import FollowUpResponse, PatchResponse
from app.nemotron import FOLLOW_UP_SCHEMA, PATCH_SCHEMA
from app.prompts import SYSTEM_PROMPT_EVALUATE, SYSTEM_PROMPT_FOLLOW_UP


class FollowUpSemanticsTests(unittest.TestCase):
    def test_local_only_repair_flow_is_resolved_not_irrelevant(self) -> None:
        response = FollowUpResponse(
            result="RESOLVED_BY_CONTEXT",
            explanation=(
                "Uninstall removes local state, then re-pairing and a Gmail rescan "
                "rebuild the ledger. The remaining re-onboarding friction is accepted."
            ),
            follow_up_question="Will the rescan rebuild the ledger?",
        )

        self.assertEqual(response.result, "RESOLVED_BY_CONTEXT")
        self.assertIsNone(response.follow_up_question)
        self.assertIn("RESOLVED_BY_CONTEXT", FOLLOW_UP_SCHEMA["properties"]["result"]["enum"])

    def test_resolved_context_and_out_of_scope_are_distinct_prompt_rules(self) -> None:
        self.assertIn("genuinely never applied", SYSTEM_PROMPT_FOLLOW_UP)
        self.assertIn("acceptable tradeoff", SYSTEM_PROMPT_FOLLOW_UP)
        self.assertIn("Never ask a follow-up question whose answer is already present", SYSTEM_PROMPT_FOLLOW_UP)


class PatchSemanticsTests(unittest.TestCase):
    def test_touch_clearance_can_close_without_modality_criterion_drift(self) -> None:
        response = PatchResponse(
            result="PATCHED",
            explanation="Touch and click clearance answer the original voice-only concern.",
            remaining_question="Does touch mirror the voice path at 9pm?",
            suggestion="Make the touch action especially visible around notification time.",
            resolution_basis="CLARIFIED",
        )

        self.assertEqual(response.result, "PATCHED")
        self.assertIsNone(response.remaining_question)
        self.assertEqual(response.resolution_basis, "CLARIFIED")
        self.assertIsNotNone(response.suggestion)
        self.assertIn("NO NEW CRITERIA", SYSTEM_PROMPT_EVALUATE)
        self.assertIn("modality-parity requirement", SYSTEM_PROMPT_EVALUATE)

    def test_patched_requires_explicit_closure_basis(self) -> None:
        with self.assertRaises(ValidationError):
            PatchResponse(
                result="PATCHED",
                explanation="The original concern is closed.",
                remaining_question=None,
                suggestion=None,
            )

    def test_open_verdict_cannot_claim_a_closure_basis(self) -> None:
        response = PatchResponse(
            result="STILL_OPEN",
            explanation="The recovery behavior remains unspecified.",
            remaining_question="What rebuilds the ledger after uninstall?",
            suggestion=None,
            resolution_basis="IMPLEMENTED",
        )

        self.assertIsNone(response.resolution_basis)
        self.assertIn("resolution_basis", PATCH_SCHEMA["required"])


if __name__ == "__main__":
    unittest.main()
