import { useMemo } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { AllCommunityModule, ModuleRegistry, themeQuartz } from 'ag-grid-community'
import { usd } from '../api.js'

ModuleRegistry.registerModules([AllCommunityModule])

const theme = themeQuartz.withParams({
  fontFamily: 'Hanken Grotesk, sans-serif', headerFontFamily: 'IBM Plex Mono, monospace', headerFontSize: 11,
  backgroundColor: '#fbf8f2', headerBackgroundColor: '#ebe4d6', oddRowBackgroundColor: '#f7f2e9',
  borderColor: '#d9d0bf', foregroundColor: '#141210', accentColor: '#ff4f1a', rowHeight: 40, headerHeight: 38,
  wrapperBorderRadius: 14,
})

const Chip = ({ value, map }) => value ? <span className={`chip ${map?.[value] || value}`}>{value.replace(/_/g, ' ')}</span> : null
const Id = ({ value }) => value ? <span className="ppid">{value}</span> : <span className="muted">-</span>

export default function Ledger({ rows, showVoice = true, height = 460 }) {
  const cols = useMemo(() => [
    { field: 'seq', headerName: '#', width: 64, cellClass: 'mono', sort: 'desc' },
    { field: 'created_at', headerName: 'When', width: 150, valueFormatter: p => new Date(p.value * 1000).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) },
    showVoice && { field: 'voice_name', headerName: 'Voice', width: 120 },
    { field: 'file_name', headerName: 'File', flex: 1, minWidth: 170 },
    { field: 'user_name', headerName: 'Used by', width: 200 },
    { field: 'seconds', headerName: 'Minutes', width: 100, cellClass: 'mono', valueFormatter: p => (p.value / 60).toFixed(2), aggFunc: 'sum' },
    { field: 'is_clone', headerName: 'Voice type', width: 120, cellRenderer: p => <span className={`chip ${p.value ? 'clone' : 'orig'}`}>{p.value ? 'AI clone' : 'original'}</span> },
    { field: 'use_type', headerName: 'Use', width: 110 },
    { field: 'confidence', headerName: 'Match', width: 90, cellClass: 'mono', valueFormatter: p => `${Math.round(p.value * 100)}%` },
    { field: 'decision', headerName: 'Decision', width: 115, cellRenderer: Chip },
    { field: 'amount_cents', headerName: 'Billed', width: 100, cellClass: 'mono', valueFormatter: p => usd(p.value) },
    { field: 'royalty_cents', headerName: 'Royalty', width: 100, cellClass: 'mono', valueFormatter: p => usd(p.value) },
    { field: 'platform_fee_cents', headerName: 'Platform fee', width: 120, cellClass: 'mono', valueFormatter: p => usd(p.value) },
    { field: 'invoice_id', headerName: 'PayPal invoice', width: 230, cellRenderer: Id },
    { field: 'payout_batch_id', headerName: 'PayPal payout', width: 160, cellRenderer: Id },
    { field: 'payout_fee_cents', headerName: 'Payout fee', width: 110, cellClass: 'mono', valueFormatter: p => p.value == null ? '-' : usd(p.value) },
    { field: 'status', headerName: 'Status', width: 140, cellRenderer: p => <Chip value={p.value} map={{ paid_out: 'bill', payout_sent: 'bill', invoiced: 'offer', blocked: 'blocked', owner_review: 'review', free: 'free', pending_invoice: 'review' }} /> },
    { field: 'hash', headerName: 'Ledger hash', width: 150, cellClass: 'mono', valueFormatter: p => p.value?.slice(0, 12) + '…' },
  ].filter(Boolean), [showVoice])

  return (
    <div className="ledger-grid" style={{ height }}>
      <AgGridReact theme={theme} rowData={rows} columnDefs={cols} defaultColDef={{ sortable: true, filter: true, resizable: true }}
        pagination paginationPageSize={20} paginationPageSizeSelector={false} animateRows
        overlayNoRowsTemplate="No uses yet. Run a scan from Pre-clear audio." />
    </div>
  )
}
