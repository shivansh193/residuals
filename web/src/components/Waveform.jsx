import { useEffect, useRef, useState } from 'react'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js'
import { tc, voiceColor } from '../api.js'

/** Waveform with matched segments painted as regions. Calls onTime(t) while playing. */
export default function Waveform({ url, segments = [], onTime, seekTo }) {
  const el = useRef(null)
  const ws = useRef(null)
  const [playing, setPlaying] = useState(false)
  const [t, setT] = useState(0)
  const [dur, setDur] = useState(0)

  useEffect(() => {
    if (!el.current || !url) return
    const regions = RegionsPlugin.create()
    const w = WaveSurfer.create({
      container: el.current, url, height: 84, barWidth: 2, barGap: 1, barRadius: 2,
      waveColor: '#b9ae9b', progressColor: '#141210', cursorColor: '#ff4f1a', cursorWidth: 2,
      normalize: true, plugins: [regions],
    })
    ws.current = w
    w.on('ready', () => {
      setDur(w.getDuration())
      for (const s of segments) {
        if (!s.voice_id) continue
        regions.addRegion({ start: s.start, end: s.end, color: voiceColor(s.voice_id) + '33', drag: false, resize: false })
      }
    })
    const tick = (x) => { setT(x); onTime && onTime(x) }
    w.on('timeupdate', tick)
    w.on('play', () => setPlaying(true))
    w.on('pause', () => setPlaying(false))
    return () => w.destroy()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, JSON.stringify(segments.map(s => [s.start, s.end, s.voice_id]))])

  useEffect(() => { if (seekTo != null && ws.current && dur) ws.current.setTime(seekTo) }, [seekTo, dur])

  return (
    <div>
      <div ref={el} style={{ background: 'var(--paper)', borderRadius: 10, padding: '8px 6px' }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 8 }}>
        <button className="btn sm" onClick={() => ws.current && ws.current.playPause()} disabled={!dur}>
          {playing ? '❚❚ Pause' : '▶ Play'}
        </button>
        <span className="mono small">{tc(t)} / {tc(dur)}</span>
      </div>
    </div>
  )
}
