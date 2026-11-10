<!-- Generated file — do not edit; regenerated with the SDK. -->

# ResidualsApiClient — ungrouped operations

Accessor: `client` (the client itself) · Source: `src/client.ts` · 2 operations · Request and error types: namespace `ResidualsApiClient`

Operations the spec leaves untagged are methods on the client rather than on a resource, so there is no accessor property to go through. The request type still lives in a namespace merged onto the exported class, so you write `ResidualsApiClient.GetPolicyRequest`.

**Type sources**: every type an operation names, with the file that declares it and the schema value exported beside it. Import every name from `residuals-api`; the `Source` path is where to **read** the shape, never what to import. `ApiError`, the runtime error family and the file vocabulary are excluded — see sdk-map.md.

### getPolicy

- **Signature**: `getPolicy(request: ResidualsApiClient.GetPolicyRequest, options?: RequestOptions): ApiPromise<PolicyOut, ResidualsApiClient.GetPolicyError>`
- **Wire**: `GET /policy/{voice_id}`
- **Auth**: none — public; no credential is sent
- **Request body**: none — no `Content-Type` header is sent
- **Returns**: `PolicyOut`
- **Error**: `ResidualsApiError` with `kind: "api"`, an instance of `ResidualsApiClient.GetPolicyError` — **typed arms**, narrowed on `err.payload.kind`
- **Error arms**: `"httpValidationError"` [422] `HttpValidationError` · `"undeclared"` [any other] `rawBody: ArrayBuffer`

**Fields** — `ResidualsApiClient.GetPolicyRequest` (1):

| Field | Channel | Wire | Type | Req |
| --- | --- | --- | --- | --- |
| `voiceId` | `path` | `voice_id` | `string` | yes |

| Type | Schema value | Source |
| --- | --- | --- |
| `PolicyOut` | `policyOutSchema` | `src/models/policy-out.ts` |
| `HttpValidationError` | `httpValidationErrorSchema` | `src/models/http-validation-error.ts` |

### scan

- **Signature**: `scan(request: ResidualsApiClient.ScanRequest, options?: RequestOptions): ApiPromise<ScanResult, ResidualsApiClient.ScanError>`
- **Wire**: `POST /scan`
- **Auth**: none — public; no credential is sent
- **Request body**: `application/json` — the `body` field
- **SDK-sent**: `header Idempotency-Key` (minted per call)
- **Returns**: `ScanResult`
- **Error**: `ResidualsApiError` with `kind: "api"`, an instance of `ResidualsApiClient.ScanError` — **typed arms**, narrowed on `err.payload.kind`
- **Error arms**: `"httpValidationError"` [422] `HttpValidationError` · `"undeclared"` [any other] `rawBody: ArrayBuffer`

**Fields** — `ResidualsApiClient.ScanRequest` (1):

| Field | Channel | Type | Req |
| --- | --- | --- | --- |
| `body` | `body` | `ScanReq` | yes |

| Type | Schema value | Source |
| --- | --- | --- |
| `ScanReq` | `scanReqSchema` | `src/models/scan-req.ts` |
| `ScanResult` | `scanResultSchema` | `src/models/scan-result.ts` |
| `HttpValidationError` | `httpValidationErrorSchema` | `src/models/http-validation-error.ts` |

