from __future__ import annotations

from typing_extensions import TypedDict

from ..core import SdkBaseModel


class ScanReq(SdkBaseModel):
    file_id: str
    user_id: str


class ScanReqDict(TypedDict):
    file_id: str
    user_id: str
