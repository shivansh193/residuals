import type { ClientOptions } from "./client-options.js";
import { ApiError, type Declared, type Undeclared } from "./core/api-error.js";
import type { ApiPromise } from "./core/api-promise.js";
import type { RequestOptions } from "./core/api-request.js";
import { noneAuth } from "./core/auth/schemes.js";
import { buildCoreClientOptions } from "./core/client-options.js";
import { RawClient } from "./core/raw-client.js";
import type { ErrorDecoders } from "./core/response-decoder.js";
import * as host from "./core/runtime-environment.js";
import { uuid } from "./core/uuid.js";
import * as s from "./core/validation/index.js";
import { httpValidationErrorSchema, type HttpValidationError } from "./models/http-validation-error.js";
import { policyOutSchema, type PolicyOut } from "./models/policy-out.js";
import { scanReqSchema, type ScanReq } from "./models/scan-req.js";
import { scanResultSchema, type ScanResult } from "./models/scan-result.js";
import { buildServers, type Servers } from "./servers.js";

/**
 * Royalties for licensed AI voice clones, paid through PayPal (sandbox).
 */
export class ResidualsApiClient {
  readonly #rawClient: RawClient;
  readonly #servers: Servers;

  constructor(options: ClientOptions = {}) {
    this.#rawClient = new RawClient({
      ...buildCoreClientOptions(options, "RESIDUALS_API_CLIENT_LOG"),
      defaultHeaders: [
        { name: "User-Agent", value: "ResidualsApiClient/0.1.0 TypeScript", schema: s.string() },
        { name: "X-APIMatic-Lang", value: "TypeScript", schema: s.string() },
        { name: "X-APIMatic-Package-Version", value: "0.1.0", schema: s.string() },
        { name: "X-APIMatic-Gen-Version", value: "4.0.0", schema: s.string() },
        { name: "X-APIMatic-OS", value: host.operatingSystem(), schema: s.optional(s.string()) },
        { name: "X-APIMatic-Runtime", value: host.runtimeDescription(), schema: s.optional(s.string()) },
      ],
      defaultQuery: [],
      defaultPathParams: [],
    });

    this.#servers = buildServers(options);
  }

  /**
   * A registered voice's machine-readable licence policy
   *
   * @returns Successful Response
   *
   * @throws {@link ResidualsApiClient.GetPolicyError} when the API answers with an error status —
   * narrow on `err.payload.kind`
   *
   * @throws {@link ResidualsApiError} when no usable response was produced: a connection failure, a
   * timeout, a body that would not decode, a value that would not encode, or a credential that
   * could not be obtained
   */
  getPolicy(
    request: ResidualsApiClient.GetPolicyRequest,
    options?: RequestOptions,
  ): ApiPromise<PolicyOut, ResidualsApiClient.GetPolicyError> {
    return this.#rawClient.execute(
      {
        method: "GET",
        urlTemplate: this.#servers.default("/policy/{voice_id}"),
        auth: noneAuth,
        pathParams: [{ name: "voice_id", value: request.voiceId, schema: s.string() }],
        query: [],
        headers: [],
        body: { kind: "empty" },
      },
      {
        success: { kind: "json", schema: policyOutSchema },
        errorFactory: ResidualsApiClient.GetPolicyError,
      },
      options,
    );
  }

  /**
   * Scan audio for registered voices, apply each owner's terms, bill via PayPal
   *
   * @returns Successful Response
   *
   * @throws {@link ResidualsApiClient.ScanError} when the API answers with an error status — narrow
   * on `err.payload.kind`
   *
   * @throws {@link ResidualsApiError} when no usable response was produced: a connection failure, a
   * timeout, a body that would not decode, a value that would not encode, or a credential that
   * could not be obtained
   */
  scan(
    request: ResidualsApiClient.ScanRequest,
    options?: RequestOptions,
  ): ApiPromise<ScanResult, ResidualsApiClient.ScanError> {
    return this.#rawClient.execute(
      {
        method: "POST",
        urlTemplate: this.#servers.default("/scan"),
        auth: noneAuth,
        pathParams: [],
        query: [],
        headers: [{ name: "Idempotency-Key", value: uuid(), schema: s.string() }],
        body: { kind: "json", value: request.body, schema: scanReqSchema },
      },
      {
        success: { kind: "json", schema: scanResultSchema },
        errorFactory: ResidualsApiClient.ScanError,
      },
      options,
    );
  }
}

export namespace ResidualsApiClient {
  export type GetPolicyRequest = {
    voiceId: string;
  };

  export class GetPolicyError extends ApiError {
    declare readonly payload: Declared<"httpValidationError", HttpValidationError> | Undeclared;

    static readonly errors: ErrorDecoders<GetPolicyError> = [
      { on: 422, kind: "httpValidationError", decode: { kind: "json", schema: httpValidationErrorSchema } },
    ];
  }

  export type ScanRequest = {
    body: ScanReq;
  };

  export class ScanError extends ApiError {
    declare readonly payload: Declared<"httpValidationError", HttpValidationError> | Undeclared;

    static readonly errors: ErrorDecoders<ScanError> = [
      { on: 422, kind: "httpValidationError", decode: { kind: "json", schema: httpValidationErrorSchema } },
    ];
  }
}
