import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, secs, usd, voiceColor } from '../api.js'
import Waveform from '../components/Waveform.jsx'
import SegmentTimeline from '../components/BryntumTimeline.jsx'

const DECISION_TEXT = {
  bill: 'Licensed: billed at the owner\'s rate',
  offer: 'Not licensed: retroactive licence offered',
  blocked: 'Blocked category: no licence possible, owner alerted',
  free: 'Free under the owner\'s terms',
  review: 'Low confidence: sent to the owner for review, not billed',
}

export default function Preclear() {
  const [files, setFiles] = useState([])
  const [users, setUsers] = useState([])
  const [voices, setVoices] = useState([])
  const [fileId, setFileId] = useState('')
  const [userId, setUserId] = useState('brightline')
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [time, setTime] = useState(0)
  const [seek, setSeek] = useState(null)

  useEffect(() => {
    Promise.all([api.demoFiles(), api.users(), api.voices()]).then(([f, u, v]) => {
      setFiles(f); setUsers(u); setVoices(v); if (f[0]) setFileId(f[0].file_id)
    }).catch(e => setErr(e.message))
  }, [])
  useEffect(() => { if (fileId) { setResult(null); api.demoFile(fileId).then(setFile) } }, [fileId])

  const run = async () => {
    setBusy(true); setErr(''); setResult(null)
    try { setResult(await api.scan(fileId, userId)) } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  const segs = file?.segments || []
  return (
    <>
      <section className="page-head">
        <div className="reveal">
          <div className="eyebrow">For brands, studios and dubbing shops</div>
          <h1>Pre-clear your audio.</h1>
          <p>Upload an ad or a scene. Residuals finds every registered voice in it, AI clones included, applies each
            owner's terms and sends one PayPal invoice for the licensed minutes.</p>
        </div>
      </section>

      <div className="grid g-side">
        <div className="card reveal d1" style={{ alignSelf: 'start', display: 'grid', gap: 14 }}>
          <label className="field">You are
            <select value={userId} onChange={e => { setUserId(e.target.value); setResult(null) }}>
              {users.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
            </select>
          </label>
          <div className="small muted" style={{ marginTop: -6 }}>
            Licences held: {(users.find(u => u.id === userId)?.licensed_voice_ids || []).map(id => voices.find(v => v.id === id)?.name).filter(Boolean).join(', ') || 'none'}
          </div>
          <div className="field" style={{ fontWeight: 600, fontSize: 13 }}>Audio file</div>
          <div style={{ display: 'grid', gap: 8 }}>
            {files.map(f => (
              <button key={f.file_id} onClick={() => setFileId(f.file_id)} className="card"
                style={{ textAlign: 'left', padding: 12, cursor: 'pointer', borderColor: f.file_id === fileId ? 'var(--ink)' : 'var(--rule)', boxShadow: f.file_id === fileId ? '3px 3px 0 var(--ink)' : 'none' }}>
                <div style={{ fontWeight: 600 }}>{f.title || f.file_name}</div>
                <div className="mono small muted">{f.file_name} · {secs(f.duration_s)}</div>
              </button>
            ))}
            {!files.length && <div className="empty small">Demo files loading…</div>}
          </div>
          <button className="btn clone" onClick={run} disabled={busy || !fileId}>
            {busy ? <><span className="spinner" /> Scanning &amp; invoicing…</> : 'Scan for registered voices →'}
          </button>
          <p className="small muted" style={{ margin: 0 }}>
            The demo files were analysed in advance on a Kaggle GPU. Billing, the PayPal invoice and payouts run live.
          </p>
        </div>

        <div style={{ display: 'grid', gap: 18 }}>
          {err && <div className="err">{err}</div>}
          {file && (
            <div className="card reveal d2">
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
                <div>
                  <div className="eyebrow">Detection view</div>
                  <h3 className="serif" style={{ fontSize: 28 }}>{file.title || file.file_name}</h3>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="eyebrow">Use type (Gemini)</div>
                  <div style={{ fontWeight: 700, fontSize: 18 }}>{file.use_type}</div>
                </div>
              </div>
              <Waveform url={file.audio_url} segments={segs} onTime={setTime} seekTo={seek} />
              <div style={{ marginTop: 14 }}>
                <SegmentTimeline segments={segs} duration={file.duration_s} voices={voices} time={time} onSeek={(t) => setSeek(t + Math.random() * 1e-3)} />
              </div>
              {file.use_type_reason && <p className="small" style={{ color: 'var(--ink-2)', marginBottom: 0 }}><b>Why "{file.use_type}":</b> {file.use_type_reason}</p>}
            </div>
          )}
          {result && <Clearance result={result} />}
        </div>
      </div>
    </>
  )
}

function Clearance({ result }) {
  const inv = result.invoice
  return (
    <>
      <div className="card reveal">
        <div className="eyebrow">Pre-clearance</div>
        <h3 className="serif" style={{ fontSize: 30, marginBottom: 12 }}>
          {result.matches.length ? `${result.matches.length} registered voice${result.matches.length > 1 ? 's' : ''} found` : 'No registered voices found'}
        </h3>
        <div style={{ display: 'grid', gap: 10 }}>
          {result.matches.map(m => (
            <div key={m.id} style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 12, padding: 14, borderRadius: 12, border: '1px solid var(--rule)', background: 'var(--paper)' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span className="dot" style={{ background: voiceColor(m.voice_id) }} />
                  <b style={{ fontSize: 17 }}>{m.voice_name}</b>
                  <span className={`chip ${m.is_clone ? 'clone' : 'orig'}`}>{m.is_clone ? 'AI clone' : 'original'}</span>
                  <span className={`chip ${m.decision}`}>{m.decision}</span>
                  {m.attribution_required && <span className="chip review">credit required</span>}
                </div>
                <div className="small" style={{ color: 'var(--ink-2)', marginTop: 6 }}>{DECISION_TEXT[m.decision]}</div>
                <div className="mono small muted" style={{ marginTop: 4 }}>
                  {secs(m.seconds)} · match {Math.round(m.confidence * 100)}% · clone prob {Math.round(m.clone_prob * 100)}% · {m.use_type}
                  {m.rate_cents_per_min ? ` · ${usd(m.rate_cents_per_min)}/min` : ''} · ledger #{m.seq}
                </div>
                {m.decision === 'offer' && inv && (
                  <a className="small" href={`/api/scans/${result.scan_id}/takedown/${m.voice_id}`} target="_blank" rel="noreferrer">If declined: takedown request template →</a>
                )}
              </div>
              <div className="serif" style={{ fontSize: 34, alignSelf: 'center' }}>{m.amount_cents ? usd(m.amount_cents) : '-'}</div>
            </div>
          ))}
        </div>
      </div>
      {inv && <PayPanel inv={inv} />}
    </>
  )
}

function PayPanel({ inv }) {
  const [state, setState] = useState(null)
  const [paying, setPaying] = useState(false)
  const [err, setErr] = useState('')
  const timer = useRef(null)

  const poll = () => api.invoice(inv.id).then(setState).catch(() => {})
  useEffect(() => {
    poll()
    timer.current = setInterval(poll, 4000)
    return () => clearInterval(timer.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inv.id])

  const uses = state?.uses || []
  const paid = state?.invoice_status === 'PAID'
  const payoutSent = uses.length && uses.every(u => u.payout_batch_id)
  const payoutDone = uses.length && uses.every(u => u.status === 'paid_out')
  useEffect(() => { if (payoutDone) clearInterval(timer.current) }, [payoutDone])

  const markPaid = async () => {
    setPaying(true); setErr('')
    try { await api.sandboxPay(inv.id); poll() } catch (e) { setErr(e.message) } finally { setPaying(false) }
  }
  const step = (done, live, n, t, d) => (
    <div className={`step ${done ? 'done' : live ? 'live' : ''}`}>
      <span className="n">{done ? '✓' : live ? <span className="spinner" /> : n}</span>
      <div><div className="t">{t}</div><div className="d">{d}</div></div>
    </div>
  )
  return (
    <div className="card reveal" style={{ borderColor: 'var(--pp)', boxShadow: '4px 4px 0 var(--pp)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div className="eyebrow" style={{ color: 'var(--pp)' }}>PayPal Invoicing v2 · sandbox</div>
          <h3 className="serif" style={{ fontSize: 30 }}>{inv.offer ? 'Retroactive licence offer' : 'Licence invoice'}: {`$${inv.total}`}</h3>
          <div className="small muted">Invoice <span className="ppid">{inv.id}</span> was sent to your PayPal email.</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'start', flexWrap: 'wrap' }}>
          <a className="btn pp" href={inv.url} target="_blank" rel="noreferrer">Pay with PayPal</a>
          <button className="btn ghost sm" onClick={markPaid} disabled={paying || paid} title="Records the payment through the PayPal API, for judges without a sandbox buyer login">
            {paying ? <span className="spinner" /> : null} Mark paid (sandbox)
          </button>
        </div>
      </div>
      {err && <div className="err" style={{ marginTop: 10 }}>{err}</div>}
      <div className="rail" style={{ marginTop: 16 }}>
        {step(true, false, 1, 'Invoice created and sent', <>POST /v2/invoicing/invoices → <span className="ppid">{inv.id}</span></>)}
        {step(paid, !paid, 2, 'Waiting for payment', paid ? 'PayPal sent INVOICING.INVOICE.PAID. The webhook signature was verified by PayPal.' : 'Pay as the sandbox buyer, or use "Mark paid (sandbox)". PayPal usually sends the paid webhook within 1–2 minutes; this page updates by itself.')}
        {step(payoutSent, paid && !payoutSent, 3, 'Royalty paid out to each voice owner', payoutSent ? <>PayPal Payouts batch {[...new Set(uses.map(u => u.payout_batch_id))].map(b => <span key={b} className="ppid" style={{ marginRight: 4 }}>{b}</span>)}</> : 'POST /v1/payments/payouts, idempotent per invoice and voice')}
        {step(payoutDone, payoutSent && !payoutDone, 4, 'Payout confirmed', payoutDone ? 'PAYMENT.PAYOUTS-ITEM.SUCCEEDED received and verified.' : 'Waiting for PayPal\'s payout webhook')}
      </div>
      {uses.length > 0 && (
        <table className="mono small" style={{ width: '100%', marginTop: 10, borderCollapse: 'collapse' }}>
          <thead><tr className="muted" style={{ textAlign: 'left' }}><th>voice</th><th>billed</th><th>platform fee</th><th>royalty</th><th>PayPal payout fee</th><th>status</th></tr></thead>
          <tbody>{uses.map(u => (
            <tr key={u.id} style={{ borderTop: '1px solid var(--rule)' }}>
              <td>{u.voice_id}</td><td>{usd(u.amount_cents)}</td><td>{usd(u.platform_fee_cents)}</td><td>{usd(u.royalty_cents)}</td>
              <td>{u.payout_fee_cents == null ? '-' : usd(u.payout_fee_cents)}</td><td>{u.status.replace(/_/g, ' ')}</td>
            </tr>))}</tbody>
        </table>
      )}
      {payoutDone ? <p className="small" style={{ marginBottom: 0 }}><Link to={`/owner/${uses[0].voice_id}`}>See it in the owner's ledger →</Link></p> : null}
    </div>
  )
}
