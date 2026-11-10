import * as s from "../core/validation/index.js";
import type { JsonValue, Schema } from "../core/validation/schema.js";

export type ScanReq = {
  fileId: string;
  userId: string;
  /** Properties the service sent or accepts beyond those declared. */
  additionalProperties?: Record<string, JsonValue>;
};

export const scanReqSchema: Schema<ScanReq> = s.object<ScanReq>(
  {
    fileId: s.string(),
    userId: s.string(),
    _keysMap: {
      fileId: "file_id",
      userId: "user_id",
    },
  },
  { additionalProperties: s.json() },
);
