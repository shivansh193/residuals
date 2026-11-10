import * as s from "../core/validation/index.js";
import type { JsonValue, Schema } from "../core/validation/schema.js";
import { matchSchema, type Match } from "./match.js";
import { durationSSchema, type DurationS } from "./unions/duration-s.js";
import { invoiceSchema, type Invoice } from "./unions/invoice.js";
import { useTypeReasonSchema, type UseTypeReason } from "./unions/use-type-reason.js";

export type ScanResult = {
  scanId: string;
  fileName: string;
  useType: string;
  useTypeReason?: UseTypeReason;
  durationS?: DurationS;
  matches: Match[];
  invoice?: Invoice;
  /** Properties the service sent or accepts beyond those declared. */
  additionalProperties?: Record<string, JsonValue>;
};

export const scanResultSchema: Schema<ScanResult> = s.object<ScanResult>(
  {
    scanId: s.string(),
    fileName: s.string(),
    useType: s.string(),
    useTypeReason: s.optional(s.lazy(() => useTypeReasonSchema)),
    durationS: s.optional(s.lazy(() => durationSSchema)),
    matches: s.array(s.lazy(() => matchSchema)),
    invoice: s.optional(s.lazy(() => invoiceSchema)),
    _keysMap: {
      scanId: "scan_id",
      fileName: "file_name",
      useType: "use_type",
      useTypeReason: "use_type_reason",
      durationS: "duration_s",
    },
  },
  { additionalProperties: s.json() },
);
