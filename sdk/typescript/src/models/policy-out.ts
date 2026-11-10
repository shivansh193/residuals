import * as s from "../core/validation/index.js";
import type { JsonValue, Schema } from "../core/validation/schema.js";
import { policySchema, type Policy } from "./policy.js";

export type PolicyOut = {
  voiceId: string;
  name: string;
  termsText: string;
  policy: Policy;
  consent: Record<string, unknown>;
  /** Properties the service sent or accepts beyond those declared. */
  additionalProperties?: Record<string, JsonValue>;
};

export const policyOutSchema: Schema<PolicyOut> = s.object<PolicyOut>(
  {
    voiceId: s.string(),
    name: s.string(),
    termsText: s.string(),
    policy: policySchema,
    consent: s.record(s.string(), s.unknown()),
    _keysMap: {
      voiceId: "voice_id",
      termsText: "terms_text",
    },
  },
  { additionalProperties: s.json() },
);
