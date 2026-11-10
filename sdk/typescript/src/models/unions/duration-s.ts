import * as s from "../../core/validation/index.js";
import type { Schema } from "../../core/validation/schema.js";

export type DurationS = number;

export const durationSSchema: Schema<DurationS> = s.of<DurationS>(s.union([s.float64()]));
