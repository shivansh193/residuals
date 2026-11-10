export { ResidualsApiClient } from "./client.js";
export type { ClientOptions } from "./client-options.js";

export {
  bodyEnrolVoiceApiEnrolPostSchema,
  type BodyEnrolVoiceApiEnrolPost,
} from "./models/body-enrol-voice-api-enrol-post.js";
export { durationSSchema, type DurationS } from "./models/unions/duration-s.js";
export { httpValidationErrorSchema, type HttpValidationError } from "./models/http-validation-error.js";
export {
  httpValidationErrorErrorSchema,
  type HttpValidationErrorError,
} from "./models/http-validation-error-error.js";
export { invoiceSchema, type Invoice } from "./models/unions/invoice.js";
export { invoiceIdSchema, type InvoiceId } from "./models/unions/invoice-id.js";
export { invoiceOutSchema, type InvoiceOut } from "./models/invoice-out.js";
export { locationSchema, type Location } from "./models/unions/location.js";
export { matchSchema, type Match } from "./models/match.js";
export { policySchema, type Policy } from "./models/policy.js";
export { policyOutSchema, type PolicyOut } from "./models/policy-out.js";
export { referenceAudioSchema, type ReferenceAudio } from "./models/unions/reference-audio.js";
export { scanReqSchema, type ScanReq } from "./models/scan-req.js";
export { scanResultSchema, type ScanResult } from "./models/scan-result.js";
export { segmentSchema, type Segment } from "./models/segment.js";
export { termsReqSchema, type TermsReq } from "./models/terms-req.js";
export { textSchema, type Text } from "./models/unions/text.js";
export { useTypeReasonSchema, type UseTypeReason } from "./models/unions/use-type-reason.js";
export { validationErrorSchema, type ValidationError } from "./models/validation-error.js";
export { voiceIdSchema, type VoiceId } from "./models/unions/voice-id.js";

export {
  CoreError as ResidualsApiError,
  ResponseError,
  DecodeError,
  EncodeError,
  ConnectionError,
  TimeoutError,
  AuthError,
  PaginationError,
  ConfigurationError,
} from "./core/errors.js";
export { ApiError } from "./core/api-error.js";
export { SchemaError } from "./core/validation/schema-error.js";
export {
  defaultLoggingOptions,
  type LoggingOptions,
  type RequestLoggingOptions,
  type Logger,
  type LogDetails,
  type HttpRequestDetails,
  type RequestHeadersDetails,
  type RequestBodyDetails,
  type HttpResponseDetails,
  type ResponseHeadersDetails,
  type HttpRetryingDetails,
  type HttpFailedDetails,
  type LogLevel,
} from "./core/logging.js";
export type { ApiPromise, ApiResult } from "./core/api-promise.js";
export type { Pageable, PageableApiResult } from "./core/pagination/pageable.js";
export type { HttpMethod, RequestOptions } from "./core/api-request.js";
export type { RetryOptions, RequestRetryOptions, RetryAttempt, RetryReason } from "./core/retry.js";
export type { BinaryContent, BinaryData, BinaryErrorContent, FileData, FileInput } from "./core/binary.js";
export type { ErrorKind } from "./core/errors.js";
export type { Declared, Undeclared } from "./core/api-error.js";
export type { Schema, EnumSchema, Encoded, ValidationResult, JsonValue } from "./core/validation/schema.js";
