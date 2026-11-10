export default function Developers() {
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  return (
    <>
      <section className="page-head">
        <div className="reveal">
          <div className="eyebrow">For platforms</div>
          <h1>Content ID for voices.</h1>
          <p>A platform calls <span className="mono">POST /scan</span> on upload to pre-clear voices, and
            <span className="mono"> GET /policy/{'{voice}'}</span> to show the owner's terms before publishing.</p>
        </div>
      </section>
      <div className="grid g2">
        <div className="card reveal d1">
          <div className="eyebrow">Scan a file</div>
          <pre className="mono small" style={{ whiteSpace: 'pre-wrap', background: 'var(--ink)', color: 'var(--paper)', padding: 16, borderRadius: 10 }}>{`curl -X POST ${origin}/scan \\
  -H "Content-Type: application/json" \\
  -d '{"file_id":"brightline_ad","user_id":"brightline"}'`}</pre>
          <p className="small muted">Returns each matched voice with its seconds, clone/original label, confidence, decision and price,
            plus the PayPal invoice created for the licensed minutes.</p>
        </div>
        <div className="card reveal d2">
          <div className="eyebrow">Read a voice's terms</div>
          <pre className="mono small" style={{ whiteSpace: 'pre-wrap', background: 'var(--ink)', color: 'var(--paper)', padding: 16, borderRadius: 10 }}>{`curl ${origin}/policy/mara`}</pre>
          <p className="small muted">Machine-readable rates in cents per minute, free and blocked use types, and attribution rules.</p>
        </div>
      </div>
      <div className="grid g3" style={{ marginTop: 18 }}>
        <a className="card reveal d2" href="/docs" style={{ textDecoration: 'none' }}><b>OpenAPI explorer →</b><div className="small muted">Interactive docs served by the API</div></a>
        <a className="card reveal d3" href="/openapi.json" style={{ textDecoration: 'none' }}><b>OpenAPI spec →</b><div className="small muted">Used to generate SDKs with APIMatic</div></a>
        <a className="card reveal d4" href="https://github.com/shivansh193/residuals/tree/main/sdk" style={{ textDecoration: 'none' }}><b>SDKs (APIMatic) →</b><div className="small muted">Generated client libraries for /scan and /policy</div></a>
      </div>
    </>
  )
}
