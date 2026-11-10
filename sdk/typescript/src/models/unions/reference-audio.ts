import * as s from "../../core/validation/index.js";
import type { Schema } from "../../core/validation/schema.js";

export type ReferenceAudio = Uint8Array;

export const referenceAudioSchema: Schema<ReferenceAudio> = s.of<ReferenceAudio>(s.union([s.bytes()]));
