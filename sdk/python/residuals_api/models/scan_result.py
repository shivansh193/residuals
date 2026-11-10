from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from ..core import UNSET, Optional, SdkBaseModel
from .invoice_out import InvoiceOut, InvoiceOutDict
from .match import Match, MatchDict


class ScanResult(SdkBaseModel):
    scan_id: str
    file_name: str
    use_type: str
    use_type_reason: Optional[str] = UNSET
    duration_s: Optional[float] = UNSET
    matches: list[Match]
    invoice: Optional[InvoiceOut] = UNSET


class ScanResultDict(TypedDict):
    scan_id: str
    file_name: str
    use_type: str
    use_type_reason: NotRequired[str]
    duration_s: NotRequired[float]
    matches: list[MatchDict]
    invoice: NotRequired[InvoiceOutDict]
