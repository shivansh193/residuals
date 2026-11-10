import * as s from "../core/validation/index.js";
import type { JsonValue, Schema } from "../core/validation/schema.js";

export type InvoiceOut = {
  id: string;
  url: string;
  total: string;
  offer: boolean;
  status: string;
  /** Properties the service sent or accepts beyond those declared. */
  additionalProperties?: Record<string, JsonValue>;
};

export const invoiceOutSchema: Schema<InvoiceOut> = s.object<InvoiceOut>(
  {
    id: s.string(),
    url: s.string(),
    total: s.string(),
    offer: s.boolean(),
    status: s.string(),
  },
  { additionalProperties: s.json() },
);
