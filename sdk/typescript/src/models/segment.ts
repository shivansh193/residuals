import * as s from "../core/validation/index.js";
import type { JsonValue, Schema } from "../core/validation/schema.js";
import { textSchema, type Text } from "./unions/text.js";
import { voiceIdSchema, type VoiceId } from "./unions/voice-id.js";

export type Segment = {
  start: number;
  end: number;
  voiceId?: VoiceId;
  score: number;
  cloneProb: number;
  text?: Text;
  /** Properties the service sent or accepts beyond those declared. */
  additionalProperties?: Record<string, JsonValue>;
};

export const segmentSchema: Schema<Segment> = s.object<Segment>(
  {
    start: s.float64(),
    end: s.float64(),
    voiceId: s.optional(s.lazy(() => voiceIdSchema)),
    score: s.float64(),
    cloneProb: s.float64(),
    text: s.optional(s.lazy(() => textSchema)),
    _keysMap: {
      voiceId: "voice_id",
      cloneProb: "clone_prob",
    },
  },
  { additionalProperties: s.json() },
);
