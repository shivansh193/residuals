<!-- Generated file — do not edit; regenerated with the SDK. -->

# Client — operations

Accessor: `client` · Source: `residuals_api/client.py` · 2 operations

Each `###` block is one operation and assumes `sdk-map.md` is loaded: blocks omit what its invariants table covers and are otherwise self-contained, so chunk at block level. Signatures are the sync parsed spelling; the async and raw spellings take the same parameters (see sdk-map.md). **Type sources** names the module declaring each type an operation mentions, so resolving a body, return or error payload is a lookup rather than a search; the runtime types `RawError` and `ApiResult` are excluded.

### client.get_policy

- **Route**: `GET /policy/{voice_id}`
- **Signature**: `def get_policy(voice_id: str, *, request_options: RequestOptionsOrDict | None = None)`
  - required, positional: `voice_id`
- **Params**: `voice_id` — path
- **Returns (parsed)**: `PolicyOut`
- **Returns (raw)**: `ApiResult[PolicyOut, GetPolicyErrorBody]`
- **Error**: `GetPolicyErrorBody` — **Case A (typed)**
- **Error arms**: `HttpValidationError` [422] · `RawError` [anything unmapped]

| Type | Source |
| --- | --- |
| `PolicyOut` | `residuals_api/models/policy_out.py` |
| `GetPolicyErrorBody` | `residuals_api/errors/get_policy_error.py` |
| `HttpValidationError` | `residuals_api/models/http_validation_error.py` |

### client.scan

- **Route**: `POST /scan`
- **Signature**: `def scan(body: ScanReq | ScanReqDict, *, request_options: RequestOptionsOrDict | None = None)`
  - required, positional: `body`
- **Params**: `body` — JSON body
- **Returns (parsed)**: `ScanResult`
- **Returns (raw)**: `ApiResult[ScanResult, ScanErrorBody]`
- **Error**: `ScanErrorBody` — **Case A (typed)**
- **Error arms**: `HttpValidationError` [422] · `RawError` [anything unmapped]

| Type | Source |
| --- | --- |
| `ScanReq` | `residuals_api/models/scan_req.py` |
| `ScanReqDict` | `residuals_api/models/scan_req.py` |
| `ScanResult` | `residuals_api/models/scan_result.py` |
| `ScanErrorBody` | `residuals_api/errors/scan_error.py` |
| `HttpValidationError` | `residuals_api/models/http_validation_error.py` |

