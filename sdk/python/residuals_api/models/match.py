from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from ..core import UNSET, Optional, SdkBaseModel
from .segment import Segment, SegmentDict


class Match(SdkBaseModel):
    id: str
    seq: int
    voice_id: str
    voice_name: str
    seconds: float
    is_clone: int
    clone_prob: float
    confidence: float
    use_type: str
    decision: str
    rate_cents_per_min: int
    amount_cents: int
    platform_fee_cents: int
    royalty_cents: int
    invoice_id: Optional[str] = UNSET
    status: str
    hash: str
    attribution_required: bool = False
    segments: Optional[list[Segment]] = UNSET


class MatchDict(TypedDict):
    id: str
    seq: int
    voice_id: str
    voice_name: str
    seconds: float
    is_clone: int
    clone_prob: float
    confidence: float
    use_type: str
    decision: str
    rate_cents_per_min: int
    amount_cents: int
    platform_fee_cents: int
    royalty_cents: int
    invoice_id: NotRequired[str]
    status: str
    hash: str
    attribution_required: NotRequired[bool]
    segments: NotRequired[list[SegmentDict]]
