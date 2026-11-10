import * as s from "../../core/validation/index.js";
import type { Schema } from "../../core/validation/schema.js";

export type UseTypeReason = string;

export const useTypeReasonSchema: Schema<UseTypeReason> = s.of<UseTypeReason>(s.union([s.string()]));
