from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from ..core import UNSET, Optional, SdkBaseModel


class Segment(SdkBaseModel):
    start: float
    end: float
    voice_id: Optional[str] = UNSET
    score: float
    clone_prob: float
    text: Optional[str] = UNSET


class SegmentDict(TypedDict):
    start: float
    end: float
    voice_id: NotRequired[str]
    score: float
    clone_prob: float
    text: NotRequired[str]
