from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from ..core import UNSET, FileResponse, Optional, SdkBaseModel


class BodyEnrolVoiceApiEnrolPost(SdkBaseModel):
    name: str
    paypal_email: str
    terms_text: str
    policy_json: str
    challenge_id: str
    consent_audio: FileResponse
    liveness_audio: FileResponse
    reference_audio: Optional[FileResponse] = UNSET


class BodyEnrolVoiceApiEnrolPostDict(TypedDict):
    name: str
    paypal_email: str
    terms_text: str
    policy_json: str
    challenge_id: str
    consent_audio: FileResponse
    liveness_audio: FileResponse
    reference_audio: NotRequired[FileResponse]
