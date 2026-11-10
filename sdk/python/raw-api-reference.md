# Raw Reference

**Raw** endpoints, reached through `with_raw_response`, return `ApiResult[T, E]` and never raise for an API error. For the parsed endpoints, see [API Reference](api-reference.md).

> Source: [ResidualsApiClient](residuals_api/client.py)

<details>
<summary><code>def get_policy(voice_id: str, *, request_options: RequestOptionsOrDict | None = None) -> ApiResult[PolicyOut, GetPolicyErrorBody]</code></summary>

<dl>
<dd>

### Description

<dl>
<dd>

Send a `GET` request.

</dd>
</dl>

### Usage

<dl>
<dd>

**Sync**

```python
result = client.with_raw_response.get_policy("some example string")
match result:
    case Success(payload=payload):
        ...  # TODO: Handle 'payload' of type PolicyOut
    case Failure(error=error):
        ...  # TODO: Handle 'error' of type GetPolicyErrorBody
```

**Async**

```python
result = await async_client.with_raw_response.get_policy("some example string")
match result:
    case Success(payload=payload):
        ...  # TODO: Handle 'payload' of type PolicyOut
    case Failure(error=error):
        ...  # TODO: Handle 'error' of type GetPolicyErrorBody
```

</dd>
</dl>

### Parameters

<dl>
<dd>

| Name | Type | Description |
| --- | --- | --- |
| <code>voice_id</code> | <code>str</code> | Value sent with the request. |
| <code>request_options</code> | <code>[RequestOptionsOrDict](residuals_api/core/request_options.py) \| None</code> | Per-call overrides for this one request, such as a timeout, extra headers, or its retry count and statuses. |

</dd>
</dl>

### Response

<dl>
<dd>

**Returns**: <code>[ApiResult](residuals_api/core/results.py)&#91;[PolicyOut](residuals_api/models/policy_out.py), [GetPolicyErrorBody](residuals_api/errors/get_policy_error.py)&#93;</code>

**On `Success`**: `payload` is <code>[PolicyOut](residuals_api/models/policy_out.py)</code> -- Successful Response

**On `Failure`**: `error` is <code>[GetPolicyErrorBody](residuals_api/errors/get_policy_error.py)</code>

Mapped in first-match order -- an earlier row wins over a later range that also covers the status:

| Status | `error` is |
| --- | --- |
| 422 | <code>[HttpValidationError](residuals_api/models/http_validation_error.py)</code> |
| anything unmapped | <code>[RawError](residuals_api/core/results.py)</code> |

</dd>
</dl>

</dd>
</dl>

</details>

<details>
<summary><code>def scan(body: ScanReq | ScanReqDict, *, request_options: RequestOptionsOrDict | None = None) -> ApiResult[ScanResult, ScanErrorBody]</code></summary>

<dl>
<dd>

### Description

<dl>
<dd>

Send a `POST` request.

</dd>
</dl>

### Usage

<dl>
<dd>

**Sync**

```python
result = client.with_raw_response.scan(ScanReq(file_id="some example string", user_id="some example string"))
match result:
    case Success(payload=payload):
        ...  # TODO: Handle 'payload' of type ScanResult
    case Failure(error=error):
        ...  # TODO: Handle 'error' of type ScanErrorBody
```

**Async**

```python
result = await async_client.with_raw_response.scan(
    ScanReq(file_id="some example string", user_id="some example string")
)
match result:
    case Success(payload=payload):
        ...  # TODO: Handle 'payload' of type ScanResult
    case Failure(error=error):
        ...  # TODO: Handle 'error' of type ScanErrorBody
```

</dd>
</dl>

### Parameters

<dl>
<dd>

| Name | Type | Description |
| --- | --- | --- |
| <code>body</code> | <code>[ScanReq](residuals_api/models/scan_req.py) \| [ScanReqDict](residuals_api/models/scan_req.py)</code> | The request body. |
| <code>request_options</code> | <code>[RequestOptionsOrDict](residuals_api/core/request_options.py) \| None</code> | Per-call overrides for this one request, such as a timeout, extra headers, or its retry count and statuses. |

</dd>
</dl>

### Response

<dl>
<dd>

**Returns**: <code>[ApiResult](residuals_api/core/results.py)&#91;[ScanResult](residuals_api/models/scan_result.py), [ScanErrorBody](residuals_api/errors/scan_error.py)&#93;</code>

**On `Success`**: `payload` is <code>[ScanResult](residuals_api/models/scan_result.py)</code> -- Successful Response

**On `Failure`**: `error` is <code>[ScanErrorBody](residuals_api/errors/scan_error.py)</code>

Mapped in first-match order -- an earlier row wins over a later range that also covers the status:

| Status | `error` is |
| --- | --- |
| 422 | <code>[HttpValidationError](residuals_api/models/http_validation_error.py)</code> |
| anything unmapped | <code>[RawError](residuals_api/core/results.py)</code> |

</dd>
</dl>

</dd>
</dl>

</details>

