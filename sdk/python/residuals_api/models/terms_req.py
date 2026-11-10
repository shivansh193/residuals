from __future__ import annotations

from typing_extensions import TypedDict

from ..core import SdkBaseModel


class TermsReq(SdkBaseModel):
    terms: str


class TermsReqDict(TypedDict):
    terms: str
