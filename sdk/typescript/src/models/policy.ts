import * as s from "../core/validation/index.js";
import type { JsonValue, Schema } from "../core/validation/schema.js";

export type Policy = {
  currency: string;
  ratesCentsPerMin: Record<string, number>;
  defaultRateCentsPerMin: number;
  freeFor: string[];
  blocked: string[];
  attributionRequired: boolean;
  notes?: string;
  /** Properties the service sent or accepts beyond those declared. */
  additionalProperties?: Record<string, JsonValue>;
};

export const policySchema: Schema<Policy> = s.object<Policy>(
  {
    currency: s.string(),
    ratesCentsPerMin: s.record(s.string(), s.int()),
    defaultRateCentsPerMin: s.int(),
    freeFor: s.array(s.string()),
    blocked: s.array(s.string()),
    attributionRequired: s.boolean(),
    notes: s.optional(s.string()),
    _keysMap: {
      ratesCentsPerMin: "rates_cents_per_min",
      defaultRateCentsPerMin: "default_rate_cents_per_min",
      freeFor: "free_for",
      attributionRequired: "attribution_required",
    },
  },
  { additionalProperties: s.json() },
);
