import * as s from "../core/validation/index.js";
import type { JsonValue, Schema } from "../core/validation/schema.js";

export type TermsReq = {
  terms: string;
  /** Properties the service sent or accepts beyond those declared. */
  additionalProperties?: Record<string, JsonValue>;
};

export const termsReqSchema: Schema<TermsReq> = s.object<TermsReq>(
  {
    terms: s.string(),
  },
  { additionalProperties: s.json() },
);
