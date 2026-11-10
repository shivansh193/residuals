# Reference

**Parsed** endpoints return the typed payload and raise `ApiError` on a documented non-2xx. For the raw endpoints, see [Raw API Reference](raw-api-reference.md).

> Source: [ResidualsApiClient](residuals_api/client.py)

<details>
<summary><code>def get_policy(voice_id: str, *, request_options: RequestOptionsOrDict | None = None) -> PolicyOut</code></summary>

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
try:
    response = client.get_policy("some example string")
    # TODO: Handle 'response' of type PolicyOut
except ApiError as e:
    ...  # TODO: Handle 'e.error' of type GetPolicyErrorBody
```

**Async**

```python
try:
    response = await async_client.get_policy("some example string")
    # TODO: Handle 'response' of type PolicyOut
except ApiError as e:
    ...  # TODO: Handle 'e.error' of type GetPolicyErrorBody
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

**OnSuccess**: <code>[PolicyOut](residuals_api/models/policy_out.py)</code> -- Successful Response

**OnError**: <code>[ApiError](residuals_api/core/exceptions.py)&#91;[GetPolicyErrorBody](residuals_api/errors/get_policy_error.py)&#93;</code>

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
<summary><code>def scan(body: ScanReq | ScanReqDict, *, request_options: RequestOptionsOrDict | None = None) -> ScanResult</code></summary>

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
try:
    response = client.scan(ScanReq(file_id="some example string", user_id="some example string"))
    # TODO: Handle 'response' of type ScanResult
except ApiError as e:
    ...  # TODO: Handle 'e.error' of type ScanErrorBody
```

**Async**

```python
try:
    response = await async_client.scan(ScanReq(file_id="some example string", user_id="some example string"))
    # TODO: Handle 'response' of type ScanResult
except ApiError as e:
    ...  # TODO: Handle 'e.error' of type ScanErrorBody
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

**OnSuccess**: <code>[ScanResult](residuals_api/models/scan_result.py)</code> -- Successful Response

**OnError**: <code>[ApiError](residuals_api/core/exceptions.py)&#91;[ScanErrorBody](residuals_api/errors/scan_error.py)&#93;</code>

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

