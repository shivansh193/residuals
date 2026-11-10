import { useEffect, useRef, useState } from 'react'
import { api, usd } from '../api.js'

function Recorder({ label, hint, seconds, onDone, done }) {
  const [rec, setRec] = useState(null)
  const [left, setLeft] = useState(seconds)
  const [url, setUrl] = useState(null)
  const [err, setErr] = useState('')
  const chunks = useRef([])
  const start = async () => {
    setErr('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      chunks.current = []
      mr.ondataavailable = e => chunks.current.push(e.data)
      mr.onstop = () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(chunks.current, { type: mr.mimeType || 'audio/webm' })
        setUrl(URL.createObjectURL(blob)); onDone(blob); setRec(null)
      }
      mr.start(); setRec(mr); setLeft(seconds)
    } catch (e) { setErr('Microphone not available: ' + e.message) }
  }
  useEffect(() => {
    if (!rec) return
    const t = setInterval(() => setLeft(l => { if (l <= 1) { rec.state === 'recording' && rec.stop(); return 0 } return l - 1 }), 1000)
    return () => clearInterval(t)
  }, [rec])
  return (
    <div className="card" style={{ background: done ? 'var(--orig-soft)' : 'var(--card)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <div><b>{label}</b><div className="small muted">{hint}</div></div>
        {rec ? <button className="btn clone sm" onClick={() => rec.stop()}>● Stop ({left}s)</button>
          : <button className="btn sm" onClick={start}>{done ? 'Re-record' : '● Record'}</button>}
      </div>
      {url && <audio controls src={url} style={{ width: '100%', marginTop: 10 }} />}
      {err && <div className="err" style={{ marginTop: 8 }}>{err}</div>}
    </div>
  )
}

export default function Enrol() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [challenge, setChallenge] = useState(null)
  const [consent, setConsent] = useState(null)
  const [live, setLive] = useState(null)
  const [ref, setRef] = useState(null)
  const [terms, setTerms] = useState('$0.50 per minute for ads, free for non-profits, never for politics.')
  const [policy, setPolicy] = useState(null)
  const [busy, setBusy] = useState('')
  const [err, setErr] = useState('')
  const [result, setResult] = useState(null)

  useEffect(() => { api.enrolChallenge().then(setChallenge).catch(e => setErr(e.message)) }, [])
  const statement = `My name is ${name || '[your name]'}. I am enrolling my own voice with Residuals, and I consent to it being matched and licensed under the terms I set.`

  const parse = async () => {
    setBusy('parse'); setErr('')
    try { setPolicy(await api.parseTerms(terms)) } catch (e) { setErr(e.message) } finally { setBusy('') }
  }
  const submit = async () => {
    setBusy('enrol'); setErr('')
    const f = new FormData()
    f.append('name', name); f.append('paypal_email', email); f.append('terms_text', terms)
    f.append('policy_json', JSON.stringify(policy)); f.append('challenge_id', challenge.id)
    f.append('consent_audio', consent, 'consent.webm'); f.append('liveness_audio', live, 'liveness.webm')
    if (ref) f.append('reference_audio', ref, 'reference.webm')
    try { setResult(await api.enrol(f)) } catch (e) { setErr(e.message) } finally { setBusy('') }
  }
  const ready = name && email && consent && live && policy && challenge

  return (
    <>
      <section className="page-head">
        <div className="reveal">
          <div className="eyebrow">For voice actors, narrators and creators</div>
          <h1>Enrol your voice.</h1>
          <p>Only you can enrol your voice. You record a consent statement and read a phrase we generate on the spot,
            and Gemini checks the recordings before your voice is registered.</p>
        </div>
      </section>
      <div className="grid g2">
        <div style={{ display: 'grid', gap: 14 }} className="reveal d1">
          <div className="card" style={{ display: 'grid', gap: 12 }}>
            <label className="field">Your name<input value={name} onChange={e => setName(e.target.value)} placeholder="Name you perform under" /></label>
            <label className="field">PayPal email for royalties (sandbox)<input value={email} onChange={e => setEmail(e.target.value)} placeholder="sb-…@personal.example.com" /></label>
          </div>
          <Recorder label="1. Consent statement" seconds={20} done={!!consent} onDone={setConsent}
            hint={<>Read aloud: <i>“{statement}”</i></>} />
          <Recorder label="2. Liveness phrase" seconds={10} done={!!live} onDone={setLive}
            hint={challenge ? <>Read aloud: <b className="serif" style={{ fontSize: 20, color: 'var(--clone)' }}>“{challenge.phrase}”</b><br />This phrase is random and expires in 10 minutes, so an old recording can't pass.</> : 'Loading phrase…'} />
          <Recorder label="3. Reference speech (optional, about 60 s)" seconds={70} done={!!ref} onDone={setRef}
            hint="Read anything you like in your normal voice. It's used to build your voiceprint." />
        </div>
        <div style={{ display: 'grid', gap: 14, alignContent: 'start' }} className="reveal d2">
          <div className="card" style={{ display: 'grid', gap: 10 }}>
            <label className="field">4. Your licence terms, in plain English
              <textarea value={terms} onChange={e => { setTerms(e.target.value); setPolicy(null) }} />
            </label>
            <button className="btn" onClick={parse} disabled={busy === 'parse' || !terms.trim()}>{busy === 'parse' ? <span className="spinner" /> : null} Turn into a policy with Gemini</button>
            {policy && (
              <div style={{ background: 'var(--paper)', borderRadius: 10, padding: 12 }}>
                <div className="eyebrow" style={{ marginBottom: 6 }}>Check this is what you meant</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {Object.entries(policy.rates_cents_per_min).map(([k, c]) => <span key={k} className="chip bill">{k}: {usd(c)}/min</span>)}
                  <span className="chip review">anything else: {usd(policy.default_rate_cents_per_min)}/min</span>
                  {policy.free_for.map(k => <span key={k} className="chip free">{k}: free</span>)}
                  {policy.blocked.map(k => <span key={k} className="chip blocked">never {k}</span>)}
                  {policy.attribution_required && <span className="chip offer">credit required</span>}
                </div>
                {policy.notes && <div className="small muted" style={{ marginTop: 6 }}>Note: {policy.notes}</div>}
              </div>
            )}
          </div>
          <button className="btn clone" onClick={submit} disabled={!ready || busy === 'enrol'}>
            {busy === 'enrol' ? <><span className="spinner" /> Checking consent and liveness…</> : 'Confirm terms and enrol →'}
          </button>
          {err && <div className="err">{err}</div>}
          {result && (
            <div className={`card ${result.verified ? '' : ''}`} style={{ borderColor: result.verified ? 'var(--ok)' : 'var(--bad)' }}>
              <h3 className="serif" style={{ fontSize: 26 }}>{result.verified ? 'Consent verified' : 'Enrolment not accepted'}</h3>
              <dl className="kv" style={{ marginTop: 10 }}>
                <dt>consent</dt><dd>{result.checks.consent_ok ? 'ok' : 'failed'}: “{result.checks.consent_transcript}”</dd>
                <dt>liveness</dt><dd>{result.checks.liveness_ok ? 'ok' : 'failed'}: heard “{result.checks.liveness_transcript}”</dd>
                <dt>reason</dt><dd>{result.checks.reason}</dd>
                {result.voice_id && <><dt>voice id</dt><dd>{result.voice_id} (status: {result.status})</dd></>}
              </dl>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
