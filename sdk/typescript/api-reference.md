# Reference

> Source: [ResidualsApiClient](src/client.ts)

<details>
<summary><code>getPolicy(request: ResidualsApiClient.GetPolicyRequest, options?: RequestOptions): ApiPromise&lt;PolicyOut, ResidualsApiClient.GetPolicyError&gt;</code></summary>

<dl>
<dd>

### Direct Usage

<dl>
<dd>

```ts
try {
  const response = await client.getPolicy({ voiceId: "some example string" });
  // TODO: Handle 'response' of type PolicyOut
} catch (err) {
  // TODO: Handle 'err' of type ResidualsApiClient.GetPolicyError, discriminated with 'err.payload.kind'
}
```

</dd>
</dl>

### Usage as ApiResult

<dl>
<dd>

```ts
const result = await client.getPolicy({ voiceId: "some example string" }).asApiResult();
// TODO: Use 'result.status' and 'result.headers' to read the raw response status and headers
if (result.ok) {
  // TODO: Use 'result.value' of type PolicyOut
} else {
  // TODO: Handle 'result', discriminated with 'result.payload.kind'
}
```

</dd>
</dl>

### Parameters

<dl>
<dd>

| Name | Type | Description |
| --- | --- | --- |
| <code>voiceId</code> | <code>string</code> | - |

</dd>
</dl>

### Response

<dl>
<dd>

**Direct**: `await client.getPolicy(request)`

- **OnSuccess**: <code>[PolicyOut](src/models/policy-out.ts)</code>
- **OnError**: throws <code>[ResidualsApiClient.GetPolicyError](src/client.ts)</code>, with `err.payload` discriminated on `kind`

**As ApiResult**: `await client.getPolicy(request).asApiResult()`

- **OnSuccess**: <code>[ApiResult](src/core/api-promise.ts)&lt;PolicyOut, ResidualsApiClient.GetPolicyError&gt;</code>, with `result.value` of type <code>[PolicyOut](src/models/policy-out.ts)</code>
- **OnError**: `result.payload` discriminated on `kind`, with `result.message`

**Thrown**: <code>[ResidualsApiError](src/core/errors.ts)</code> on any operational failure — a caller abort and a programmer error stay outside the family and reach you raw

</dd>
</dl>

</dd>
</dl>

</details>

<details>
<summary><code>scan(request: ResidualsApiClient.ScanRequest, options?: RequestOptions): ApiPromise&lt;ScanResult, ResidualsApiClient.ScanError&gt;</code></summary>

<dl>
<dd>

### Direct Usage

<dl>
<dd>

```ts
try {
  const response = await client.scan({
    body: { fileId: "some example string", userId: "some example string" },
  });
  // TODO: Handle 'response' of type ScanResult
} catch (err) {
  // TODO: Handle 'err' of type ResidualsApiClient.ScanError, discriminated with 'err.payload.kind'
}
```

</dd>
</dl>

### Usage as ApiResult

<dl>
<dd>

```ts
const result = await client
  .scan({ body: { fileId: "some example string", userId: "some example string" } })
  .asApiResult();
// TODO: Use 'result.status' and 'result.headers' to read the raw response status and headers
if (result.ok) {
  // TODO: Use 'result.value' of type ScanResult
} else {
  // TODO: Handle 'result', discriminated with 'result.payload.kind'
}
```

</dd>
</dl>

### Parameters

<dl>
<dd>

| Name | Type | Description |
| --- | --- | --- |
| <code>body</code> | <code>[ScanReq](src/models/scan-req.ts)</code> | - |

</dd>
</dl>

### Response

<dl>
<dd>

**Direct**: `await client.scan(request)`

- **OnSuccess**: <code>[ScanResult](src/models/scan-result.ts)</code>
- **OnError**: throws <code>[ResidualsApiClient.ScanError](src/client.ts)</code>, with `err.payload` discriminated on `kind`

**As ApiResult**: `await client.scan(request).asApiResult()`

- **OnSuccess**: <code>[ApiResult](src/core/api-promise.ts)&lt;ScanResult, ResidualsApiClient.ScanError&gt;</code>, with `result.value` of type <code>[ScanResult](src/models/scan-result.ts)</code>
- **OnError**: `result.payload` discriminated on `kind`, with `result.message`

**Thrown**: <code>[ResidualsApiError](src/core/errors.ts)</code> on any operational failure — a caller abort and a programmer error stay outside the family and reach you raw

</dd>
</dl>

</dd>
</dl>

</details>

