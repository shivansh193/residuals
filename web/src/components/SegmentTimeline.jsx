import { tc, voiceColor } from '../api.js'

/**
 * One lane per detected speaker (registered voice or "unknown"), segments coloured by clone/original.
 * Clicking a segment seeks the audio. Same props as the Bryntum version so the two are swappable.
 */
export default function SegmentTimeline({ segments, duration, voices, time = 0, onSeek }) {
  const lanes = []
  const byLane = {}
  for (const s of segments) {
    const k = s.voice_id || 'unknown'
    if (!byLane[k]) { byLane[k] = []; lanes.push(k) }
    byLane[k].push(s)
  }
  const name = (k) => k === 'unknown' ? 'Unregistered speaker' : (voices.find(v => v.id === k)?.name || k)
  const ticks = []
  const step = duration > 90 ? 15 : duration > 40 ? 10 : 5
  for (let x = 0; x <= duration; x += step) ticks.push(x)

  return (
    <div className="seg-timeline" style={{ border: '1px solid var(--rule)', borderRadius: 12, overflow: 'hidden', background: 'var(--card)' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '170px 1fr', borderBottom: '1px solid var(--rule)', background: 'var(--paper-2)' }}>
        <div className="eyebrow" style={{ padding: '8px 12px' }}>Voice</div>
        <div style={{ position: 'relative', height: 30 }}>
          {ticks.map(x => (
            <span key={x} className="mono" style={{ position: 'absolute', left: `${(x / duration) * 100}%`, top: 8, fontSize: 10, color: 'var(--ink-3)', transform: 'translateX(-50%)' }}>{tc(x).slice(0, 5)}</span>
          ))}
        </div>
      </div>
      {lanes.map(k => (
        <div key={k} style={{ display: 'grid', gridTemplateColumns: '170px 1fr', borderBottom: '1px solid var(--rule)' }}>
          <div style={{ padding: '12px', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: 14 }}>
            <span className="dot" style={{ background: k === 'unknown' ? 'var(--ink-3)' : voiceColor(k) }} />{name(k)}
          </div>
          <div style={{ position: 'relative', height: 52 }}>
            {ticks.map(x => <span key={x} style={{ position: 'absolute', left: `${(x / duration) * 100}%`, top: 0, bottom: 0, borderLeft: '1px dashed var(--rule)' }} />)}
            {byLane[k].map((s, i) => {
              const clone = s.clone_prob >= 0.5
              const known = !!s.voice_id
              return (
                <button key={i} onClick={() => onSeek && onSeek(s.start)}
                  title={`${tc(s.start)}–${tc(s.end)} · ${known ? (clone ? 'AI clone' : 'original') : 'not registered'} · match ${(s.score ?? 0).toFixed(2)}${s.text ? '\n“' + s.text + '”' : ''}`}
                  style={{
                    position: 'absolute', top: 9, height: 34, left: `${(s.start / duration) * 100}%`, width: `max(4px, ${((s.end - s.start) / duration) * 100}%)`,
                    borderRadius: 7, cursor: 'pointer', padding: '0 6px', overflow: 'hidden', textAlign: 'left',
                    border: `1.5px solid ${known ? (clone ? 'var(--clone)' : 'var(--orig)') : 'var(--ink-3)'}`,
                    background: known ? (clone ? 'repeating-linear-gradient(135deg, var(--clone-soft) 0 6px, #ffd0bd 6px 12px)' : 'var(--orig-soft)') : 'var(--paper-2)',
                    color: known ? (clone ? '#a8300a' : 'var(--orig)') : 'var(--ink-3)', fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap',
                  }}>
                  {known ? (clone ? 'AI clone' : 'original') : ''}
                </button>
              )
            })}
          </div>
        </div>
      ))}
      <div style={{ position: 'relative', height: 0 }}>
        <span style={{ position: 'absolute', bottom: 0, height: lanes.length * 53 + 30, left: `calc(170px + (100% - 170px) * ${Math.min(1, time / (duration || 1))})`, borderLeft: '2px solid var(--clone)', pointerEvents: 'none' }} />
      </div>
      <div style={{ display: 'flex', gap: 16, padding: '8px 12px', fontSize: 12, color: 'var(--ink-2)', background: 'var(--paper-2)' }}>
        <span><span className="chip clone">AI clone</span></span>
        <span><span className="chip orig">original recording</span></span>
        <span className="muted">Hover a segment for its transcript and match score; click to play from there.</span>
      </div>
    </div>
  )
}
