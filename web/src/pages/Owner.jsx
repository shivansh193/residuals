import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, secs, usd, voiceColor } from '../api.js'
import Ledger from '../components/Ledger.jsx'

export default function Owner() {
  const { voiceId } = useParams()
  const nav = useNavigate()
  const [voices, setVoices] = useState([])
  const [rows, setRows] = useState([])
  const [alerts, setAlerts] = useState([])
  const [chain, setChain] = useState(null)
  const id = voiceId || 'mara'

  useEffect(() => { api.voices().then(setVoices) }, [])
  useEffect(() => {
    const load = () => { api.ledger(id).then(setRows); api.alerts(id).then(setAlerts); api.verifyLedger().then(setChain); api.voices().then(setVoices) }
    load()
    const t = setInterval(load, 8000)
    return () => clearInterval(t)
  }, [id])

  const v = voices.find(x => x.id === id)
  if (!v) return <div className="empty" style={{ marginTop: 40 }}>Loading…</div>
  const p = v.policy
  return (
    <>
      <section className="page-head">
        <div className="reveal">
          <div className="eyebrow">Voice owner dashboard</div>
          <h1>{v.name}</h1>
          <p>Where this voice was used, what it earned, and what needs attention.</p>
        </div>
        <label className="field" style={{ width: 240 }}>Viewing as
          <select value={id} onChange={e => nav(`/owner/${e.target.value}`)}>
            {voices.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}
          </select>
        </label>
      </section>

      <div className="grid g3">
        <div className="card ink reveal d1">
          <div className="stat"><span className="k" style={{ color: '#b9ae9b' }}>Royalties paid out</span><span className="v" style={{ color: 'var(--clone)' }}>{usd(v.stats.earned)}</span></div>
          <div className="small" style={{ color: '#b9ae9b', marginTop: 8 }}>via PayPal Payouts · {usd(v.stats.pending)} pending on unpaid invoices</div>
        </div>
        <div className="card reveal d2"><div className="stat"><span className="k">Detected uses</span><span className="v">{v.stats.n}</span></div>
          <div className="small muted" style={{ marginTop: 8 }}>{secs(v.stats.secs)} of audio across all files</div></div>
        <div className="card reveal d3"><div className="stat"><span className="k">Ledger integrity</span>
          <span className="v" style={{ fontSize: 30, color: chain?.valid ? 'var(--ok)' : 'var(--bad)' }}>{chain ? (chain.valid ? 'Hash chain intact' : `Broken at #${chain.first_bad_seq}`) : '…'}</span></div>
          <div className="small muted" style={{ marginTop: 8 }}>{chain?.entries ?? 0} entries, each SHA-256 linked to the previous one</div></div>
      </div>

      <div className="grid g2" style={{ marginTop: 18 }}>
        <div className="card reveal d2">
          <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
            <div style={{ width: 54, height: 54, borderRadius: 14, background: voiceColor(v.id), display: 'grid', placeItems: 'center', color: '#fff', fontFamily: 'var(--serif)', fontSize: 30 }}>{v.name[0]}</div>
            <div>
              <h3 className="serif" style={{ fontSize: 26 }}>Voice card</h3>
              <div className="small muted">Enrolled {new Date(v.enrolled_at * 1000).toLocaleDateString()} · {v.synthetic ? 'fully synthetic demo persona' : 'self-enrolled with liveness check'}</div>
            </div>
          </div>
          <blockquote className="serif" style={{ fontSize: 22, margin: '16px 0', borderLeft: '3px solid var(--clone)', paddingLeft: 14 }}>“{v.terms_text}”</blockquote>
          <div className="eyebrow" style={{ marginBottom: 6 }}>Structured policy (parsed by Gemini, confirmed by owner)</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {Object.entries(p.rates_cents_per_min).map(([k, c]) => <span key={k} className="chip bill">{k}: {usd(c)}/min</span>)}
            <span className="chip review">anything else: {usd(p.default_rate_cents_per_min)}/min</span>
            {p.free_for.map(k => <span key={k} className="chip free">{k}: free</span>)}
            {p.blocked.map(k => <span key={k} className="chip blocked">never {k}</span>)}
            {p.attribution_required && <span className="chip offer">credit required</span>}
          </div>
          <p className="small muted" style={{ marginBottom: 0 }}>Public at <a className="mono" href={`/policy/${v.id}`}>/policy/{v.id}</a> so platforms can pre-clear.</p>
        </div>
        <div className="card reveal d3">
          <h3 className="serif" style={{ fontSize: 26, marginBottom: 10 }}>Alerts</h3>
          {alerts.length === 0 && <div className="empty small">No alerts. Blocked-category uses and low-confidence matches appear here.</div>}
          <div style={{ display: 'grid', gap: 8, maxHeight: 300, overflow: 'auto' }}>
            {alerts.map(a => (
              <div key={a.id} style={{ padding: 12, borderRadius: 10, background: a.kind === 'blocked_use' ? '#f9dedc' : 'var(--paper-2)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <span className={`chip ${a.kind === 'blocked_use' ? 'blocked' : 'review'}`}>{a.kind === 'blocked_use' ? 'Blocked use' : 'Needs review'}</span>
                  <span className="mono small muted">{new Date(a.created_at * 1000).toLocaleString()}</span>
                </div>
                <div className="small" style={{ marginTop: 6 }}>{a.message}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="section-title"><h2>Usage ledger</h2><span className="eyebrow">AG Grid · every row hash-chained</span></div>
      <Ledger rows={rows} showVoice={false} />
    </>
  )
}
