from __future__ import annotations

from typing_extensions import TypedDict

from ..core import SdkBaseModel


class InvoiceOut(SdkBaseModel):
    id: str
    url: str
    total: str
    offer: bool
    status: str


class InvoiceOutDict(TypedDict):
    id: str
    url: str
    total: str
    offer: bool
    status: str
