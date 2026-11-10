import * as s from "../core/validation/index.js";
import type { JsonValue, Schema } from "../core/validation/schema.js";
import { segmentSchema, type Segment } from "./segment.js";
import { invoiceIdSchema, type InvoiceId } from "./unions/invoice-id.js";

export type Match = {
  id: string;
  seq: number;
  voiceId: string;
  voiceName: string;
  seconds: number;
  isClone: number;
  cloneProb: number;
  confidence: number;
  useType: string;
  decision: string;
  rateCentsPerMin: number;
  amountCents: number;
  platformFeeCents: number;
  royaltyCents: number;
  invoiceId?: InvoiceId;
  status: string;
  hash: string;
  /** @default false */
  attributionRequired?: boolean;
  segments?: Segment[];
  /** Properties the service sent or accepts beyond those declared. */
  additionalProperties?: Record<string, JsonValue>;
};

export const matchSchema: Schema<Match> = s.object<Match>(
  {
    id: s.string(),
    seq: s.int(),
    voiceId: s.string(),
    voiceName: s.string(),
    seconds: s.float64(),
    isClone: s.int(),
    cloneProb: s.float64(),
    confidence: s.float64(),
    useType: s.string(),
    decision: s.string(),
    rateCentsPerMin: s.int(),
    amountCents: s.int(),
    platformFeeCents: s.int(),
    royaltyCents: s.int(),
    invoiceId: s.optional(s.lazy(() => invoiceIdSchema)),
    status: s.string(),
    hash: s.string(),
    attributionRequired: s.defaulted(s.boolean(), false),
    segments: s.optional(s.array(s.lazy(() => segmentSchema))),
    _keysMap: {
      voiceId: "voice_id",
      voiceName: "voice_name",
      isClone: "is_clone",
      cloneProb: "clone_prob",
      useType: "use_type",
      rateCentsPerMin: "rate_cents_per_min",
      amountCents: "amount_cents",
      platformFeeCents: "platform_fee_cents",
      royaltyCents: "royalty_cents",
      invoiceId: "invoice_id",
      attributionRequired: "attribution_required",
    },
  },
  { additionalProperties: s.json() },
);
