import * as s from "../../core/validation/index.js";
import type { Schema } from "../../core/validation/schema.js";

export type VoiceId = string;

export const voiceIdSchema: Schema<VoiceId> = s.of<VoiceId>(s.union([s.string()]));
