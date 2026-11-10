from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from ..core import SdkBaseModel


class Policy(SdkBaseModel):
    currency: str
    rates_cents_per_min: dict[str, int]
    default_rate_cents_per_min: int
    free_for: list[str]
    blocked: list[str]
    attribution_required: bool
    notes: str = ""


class PolicyDict(TypedDict):
    currency: str
    rates_cents_per_min: dict[str, int]
    default_rate_cents_per_min: int
    free_for: list[str]
    blocked: list[str]
    attribution_required: bool
    notes: NotRequired[str]
