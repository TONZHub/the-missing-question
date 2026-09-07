from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


Severity = Literal["low", "medium", "high", "critical"]


class AnalyzeRequest(BaseModel):
    context: str = Field(min_length=1, max_length=100_000)
    mode: Literal["manual", "sidecar"] = "manual"


class AnalyzeResponse(BaseModel):
    status: Literal["CLEAR", "POKE_HOLE"]
    question: str | None = None
    assumption: str | None = None
    why_now: str | None = None
    severity: Severity | None = None
    failure_if_ignored: str | None = None
    evidence: str | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "AnalyzeResponse":
        concern_fields = (
            self.question,
            self.assumption,
            self.why_now,
            self.severity,
            self.failure_if_ignored,
            self.evidence,
        )

        if self.status == "CLEAR":
            if any(value is not None for value in concern_fields):
                raise ValueError("CLEAR responses must not include concern fields.")
            return self

        if any(value is None or (isinstance(value, str) and not value.strip()) for value in concern_fields):
            raise ValueError("POKE_HOLE responses must include all concern fields.")
        return self


class FollowUpRequest(BaseModel):
    original_concern: AnalyzeResponse
    follow_up: str = Field(min_length=1, max_length=50_000)
    updated_context: str = Field(default="", max_length=100_000)

    @model_validator(mode="after")
    def concern_must_be_hole(self) -> "FollowUpRequest":
        if self.original_concern.status != "POKE_HOLE":
            raise ValueError("original_concern must have status POKE_HOLE.")
        return self


class FollowUpResponse(BaseModel):
    result: Literal["VALID_CONCERN", "OUT_OF_SCOPE", "NEEDS_CONTEXT"]
    explanation: str = Field(min_length=1)
    follow_up_question: str | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "FollowUpResponse":
        if self.result == "OUT_OF_SCOPE":
            self.follow_up_question = None
            return self

        if self.result == "NEEDS_CONTEXT":
            if not self.follow_up_question or not self.follow_up_question.strip():
                raise ValueError("NEEDS_CONTEXT responses must include one follow_up_question.")
            return self

        # VALID_CONCERN may include one sharper question, but it is optional.
        if self.follow_up_question is not None and not self.follow_up_question.strip():
            self.follow_up_question = None
        return self


class EvaluatePatchRequest(BaseModel):
    original_concern: AnalyzeResponse
    resolution: str = Field(min_length=1, max_length=50_000)
    updated_context: str = Field(default="", max_length=100_000)

    @model_validator(mode="after")
    def concern_must_be_hole(self) -> "EvaluatePatchRequest":
        if self.original_concern.status != "POKE_HOLE":
            raise ValueError("original_concern must have status POKE_HOLE.")
        return self


class PatchResponse(BaseModel):
    result: Literal["PATCHED", "PARTIALLY_PATCHED", "STILL_OPEN"]
    explanation: str = Field(min_length=1)
    remaining_question: str | None = None
    suggestion: str | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "PatchResponse":
        if self.suggestion is not None and not self.suggestion.strip():
            self.suggestion = None

        if self.result == "PATCHED":
            self.remaining_question = None
            return self

        if not self.remaining_question or not self.remaining_question.strip():
            raise ValueError(
                "PARTIALLY_PATCHED and STILL_OPEN responses must include remaining_question."
            )
        return self
