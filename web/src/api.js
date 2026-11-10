async function req(method, path, body) {
  const r = await fetch(path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  const text = await r.text()
  let data
  try { data = text ? JSON.parse(text) : null } catch { data = text }
  if (!r.ok) throw new Error((data && data.detail) || `${r.status} ${r.statusText}`)
  return data
}

export const api = {
  voices: () => req('GET', '/api/voices'),
  users: () => req('GET', '/api/users'),
  demoFiles: () => req('GET', '/api/demo-files'),
  demoFile: (id) => req('GET', `/api/demo-files/${id}`),
  scan: (file_id, user_id) => req('POST', '/scan', { file_id, user_id }),
  scanById: (id) => req('GET', `/api/scans/${id}`),
  invoice: (id) => req('GET', `/api/invoices/${id}`),
  sandboxPay: (id) => req('POST', `/api/invoices/${id}/sandbox-pay`),
  ledger: (voice_id) => req('GET', '/api/ledger' + (voice_id ? `?voice_id=${voice_id}` : '')),
  verifyLedger: () => req('GET', '/api/ledger/verify'),
  alerts: (voice_id) => req('GET', '/api/alerts' + (voice_id ? `?voice_id=${voice_id}` : '')),
  parseTerms: (terms) => req('POST', '/api/terms/parse', { terms }),
  policy: (id) => req('GET', `/policy/${id}`),
  webhookEvents: () => req('GET', '/api/webhook-events'),
  enrolChallenge: () => req('GET', '/api/enrol/challenge'),
  enrol: (form) => fetch('/api/enrol', { method: 'POST', body: form }).then(async r => {
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.detail || r.statusText)
    return d
  }),
}

export const usd = (cents) => `$${(cents / 100).toFixed(2)}`
export const secs = (s) => {
  const m = Math.floor(s / 60), r = Math.round(s % 60)
  return m ? `${m}m ${String(r).padStart(2, '0')}s` : `${r}s`
}
export const tc = (s) => {
  const m = Math.floor(s / 60), r = (s % 60).toFixed(1)
  return `${String(m).padStart(2, '0')}:${r.padStart(4, '0')}`
}
export const VOICE_COLORS = { mara: '#ff4f1a', theo: '#0f6e6a', juno: '#7a3cff', silas: '#b26a00', ivy: '#0070e0' }
export const voiceColor = (id) => VOICE_COLORS[id] || '#4a443c'
