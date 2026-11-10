import { useEffect, useMemo, useRef } from 'react'
import { BryntumScheduler } from '@bryntum/scheduler-react'
import '@bryntum/scheduler/scheduler.css'
import '@bryntum/scheduler/svalbard-light.css'
import { tc, voiceColor } from '../api.js'

// Bryntum schedules dates, so audio seconds are mapped onto a fixed day.
const BASE = new Date(2026, 0, 1, 0, 0, 0).getTime()
const at = (s) => new Date(BASE + s * 1000)

/** Bryntum Scheduler: one row per detected voice, one bar per matched segment (clone hatched orange, original teal). */
export default function BryntumTimeline({ segments, duration, voices, time = 0, onSeek }) {
  const ref = useRef(null)
  const { resources, events } = useMemo(() => {
    const lanes = []
    for (const s of segments) {
      const k = s.voice_id || 'unknown'
      if (!lanes.includes(k)) lanes.push(k)
    }
    return {
      resources: lanes.map(k => ({
        id: k, name: k === 'unknown' ? 'Unregistered speaker' : (voices.find(v => v.id === k)?.name || k),
        eventColor: k === 'unknown' ? 'gray' : null, swatch: k === 'unknown' ? '#8a8174' : voiceColor(k),
      })),
      events: segments.map((s, i) => {
        const known = !!s.voice_id, clone = s.clone_prob >= 0.5
        return {
          id: i + 1, resourceId: s.voice_id || 'unknown', startDate: at(s.start), endDate: at(s.end),
          name: known ? (clone ? 'AI clone' : 'original') : 'not registered',
          cls: known ? (clone ? 'seg-clone' : 'seg-orig') : 'seg-unknown',
          seg: s,
        }
      }),
    }
  }, [segments, voices])

  const step = duration > 90 ? 15 : duration > 40 ? 10 : 5
  const config = useMemo(() => ({
    startDate: at(0), endDate: at(Math.ceil(duration)), rowHeight: 50, barMargin: 8, height: 90 + resources.length * 50,
    readOnly: true, eventStyle: 'border', zoomOnMouseWheel: false, zoomOnTimeAxisDoubleClick: false,
    viewPreset: {
      base: 'secondAndMinute', tickWidth: 30, displayDateFormat: 'mm:ss',
      timeResolution: { unit: 'millisecond', increment: 100 },
      headers: [{ unit: 'second', increment: step, dateFormat: 'mm:ss' }],
    },
    columns: [{
      text: 'Voice', field: 'name', width: 180,
      renderer: ({ record }) => ({
        children: [
          { tag: 'span', style: `display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;background:${record.swatch}` },
          { tag: 'b', text: record.name },
        ],
      }),
    }],
    features: {
      eventDrag: false, eventResize: false, eventEdit: false, eventMenu: false, scheduleMenu: false, cellMenu: false,
      eventDragCreate: false, timeRanges: { showCurrentTimeLine: false },
      eventTooltip: {
        template: ({ eventRecord: e }) => {
          const s = e.seg
          return `<b>${tc(s.start)} – ${tc(s.end)}</b><br>${e.name} · match ${s.score.toFixed(2)} · clone prob ${Math.round(s.clone_prob * 100)}%` +
            (s.text ? `<br><i>“${s.text.replace(/</g, '&lt;')}”</i>` : '')
        },
      },
    },
    eventRenderer: ({ eventRecord, renderData }) => {
      renderData.cls.add(eventRecord.cls)
      return eventRecord.name
    },
    timeRanges: [{ id: 'playhead', startDate: at(0), cls: 'playhead' }],
  }), [duration, resources.length, step])

  useEffect(() => {
    const sch = ref.current?.instance
    const r = sch?.timeRangeStore?.getById('playhead')
    if (r) r.startDate = at(Math.min(time, duration))
  }, [time, duration])

  return (
    <div className="bryntum-wrap">
      <BryntumScheduler ref={ref} {...config} resources={resources} events={events}
        onEventClick={({ eventRecord }) => onSeek && onSeek(eventRecord.seg.start)} />
      <div style={{ display: 'flex', gap: 16, padding: '8px 12px', fontSize: 12, color: 'var(--ink-2)', background: 'var(--paper-2)', alignItems: 'center', flexWrap: 'wrap' }}>
        <span className="chip clone">AI clone</span><span className="chip orig">original recording</span>
        <span className="muted">Bryntum Scheduler. Hover a segment for its transcript and scores; click to play from there.</span>
      </div>
    </div>
  )
}
