import { Link } from 'react-router-dom'

const steps = [
  ['01', 'Enrol, with consent', 'The owner records a consent statement and reads a random liveness phrase aloud. Gemini checks that the right words were spoken, so nobody can enrol someone else from an old recording.'],
  ['02', 'Set terms in plain English', '"$0.50 a minute for ads, free for non-profits, never for politics." Gemini turns that into a machine-readable policy, and the owner confirms it.'],
  ['03', 'Detect the voice, even as a clone', 'Speech detection, speaker embeddings (ECAPA) matched against enrolled voices, a clone-vs-original detector, transcription, and an LLM that classifies the use.'],
  ['04', 'Bill through PayPal', 'Minutes × the owner\'s rate becomes a PayPal invoice (Invoicing v2). Unlicensed use gets a retroactive licence offer instead of a lawsuit.'],
  ['05', 'Pay the owner automatically', 'PayPal\'s signed INVOICING.INVOICE.PAID webhook triggers a PayPal Payout of the royalty to the owner, with the platform fee shown openly.'],
]

export default function Home() {
  return (
    <>
      <section className="page-head" style={{ paddingTop: 64 }}>
        <div className="reveal">
          <div className="eyebrow">Royalties for licensed AI voice clones</div>
          <h1 style={{ fontSize: 'clamp(48px, 8vw, 104px)', marginTop: 12 }}>
            Your voice.<br /><em style={{ color: 'var(--clone)' }}>Your terms.</em><br />Your royalties.
          </h1>
          <p style={{ fontSize: 18, maxWidth: 620, marginTop: 20 }}>
            AI voice clones are in ads, audiobooks, games and dubbing, and the people they belong to rarely know or get paid.
            Residuals finds a registered voice in any audio, even as an AI clone, meters the minutes, invoices the user
            through PayPal, and pays the owner their royalty by PayPal Payout.
          </p>
          <div style={{ display: 'flex', gap: 10, marginTop: 24, flexWrap: 'wrap' }}>
            <Link className="btn clone" to="/preclear">Try it: pre-clear an ad →</Link>
            <Link className="btn ghost" to="/owner">See an owner's royalties</Link>
          </div>
        </div>
      </section>

      <div className="section-title"><h2>How it works</h2><span className="eyebrow">PayPal + AI, end to end</span></div>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))' }}>
        {steps.map(([n, t, d], i) => (
          <div key={n} className={`card reveal d${Math.min(i, 4)}`}>
            <div className="mono" style={{ color: 'var(--clone)', fontSize: 13 }}>{n}</div>
            <h3 className="serif" style={{ fontSize: 26, margin: '6px 0 8px' }}>{t}</h3>
            <p className="small" style={{ margin: 0, color: 'var(--ink-2)' }}>{d}</p>
          </div>
        ))}
      </div>

      <div className="section-title"><h2>The one rule</h2></div>
      <div className="card ink" style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 24, alignItems: 'center' }}>
        <div className="serif" style={{ fontSize: 64, lineHeight: 1, color: 'var(--clone)' }}>Consent first.</div>
        <p style={{ margin: 0, color: '#d8d0c2' }}>
          Only voices whose owners enrolled themselves, with a consent recording and a live liveness phrase, can be registered.
          Detections below the confidence threshold are never billed automatically: they go to the owner for review.
          Every voice in this demo is a fictional, fully synthetic persona. No real person's voice was recorded or cloned.
        </p>
      </div>
    </>
  )
}
