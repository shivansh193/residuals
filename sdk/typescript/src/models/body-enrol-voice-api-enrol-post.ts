import * as s from "../core/validation/index.js";
import type { JsonValue, Schema } from "../core/validation/schema.js";
import { referenceAudioSchema, type ReferenceAudio } from "./unions/reference-audio.js";

export type BodyEnrolVoiceApiEnrolPost = {
  name: string;
  paypalEmail: string;
  termsText: string;
  policyJson: string;
  challengeId: string;
  consentAudio: Uint8Array;
  livenessAudio: Uint8Array;
  referenceAudio?: ReferenceAudio;
  /** Properties the service sent or accepts beyond those declared. */
  additionalProperties?: Record<string, JsonValue>;
};

export const bodyEnrolVoiceApiEnrolPostSchema: Schema<BodyEnrolVoiceApiEnrolPost> =
  s.object<BodyEnrolVoiceApiEnrolPost>(
    {
      name: s.string(),
      paypalEmail: s.string(),
      termsText: s.string(),
      policyJson: s.string(),
      challengeId: s.string(),
      consentAudio: s.bytes(),
      livenessAudio: s.bytes(),
      referenceAudio: s.optional(s.lazy(() => referenceAudioSchema)),
      _keysMap: {
        paypalEmail: "paypal_email",
        termsText: "terms_text",
        policyJson: "policy_json",
        challengeId: "challenge_id",
        consentAudio: "consent_audio",
        livenessAudio: "liveness_audio",
        referenceAudio: "reference_audio",
      },
    },
    { additionalProperties: s.json() },
  );
