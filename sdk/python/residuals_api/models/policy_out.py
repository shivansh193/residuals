from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict

from ..core import SdkBaseModel
from .policy import Policy, PolicyDict


class PolicyOut(SdkBaseModel):
    voice_id: str
    name: str
    terms_text: str
    policy: Policy
    consent: Any


class PolicyOutDict(TypedDict):
    voice_id: str
    name: str
    terms_text: str
    policy: PolicyDict
    consent: Any
