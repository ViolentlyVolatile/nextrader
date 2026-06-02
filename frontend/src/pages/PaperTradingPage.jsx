import { useState, useEffect, useRef, useCallback } from 'react'
import { startPaper, stopPaper, getPaperStatus, getPaperSignals, getPaperTrades } from '../api/client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Play, Square, Wifi, WifiOff, TrendingUp, TrendingDown, Activity, AlertTriangle } from 'lucide-react'

// ── Reusable confidence bar ───────────────────────────────────────────────
const ConfBar = ({ value }) => {
  const color = value >= 70 ? '#22c55e' : value >= 60 ? '#eab308' : '#ef4444'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-800 rounded-full h-1.5">
        <div className="h-1.5 rounded-full transition-all" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="text-xs font-bold w-10 text-right" style={{ color }}>{value?.toFixed(1)}%</span>
    </div>
  )
}

// ── Metric card ───────────────────────────────────────────────────────────
const MCard = ({ label, value, color = 'text-gray-100', sub }) => (
  <div className="bg-gray-900 border border-gray-800 rounded-xl p-3">
    <div className="text-gray-500 text-xs mb-1">{label}</div>
    <div className={`text-lg font-bold font-mono ${color}`}>{value}</div>
    {sub && <div className="text-gray-600 text-xs mt-1">{sub}</div>}
  </div>
)

export default function PaperTradingPage() {
  const [running,    setRunning]    = useState(false)
  const [connected,  setConnected]  = useState(false)
  const [portfolio,  setPortfolio]  = useState(null)
  const [signals,    setSignals]    = useState([])
  const [trades,     setTrades]     = useState([])
  const [ticks,      setTicks]      = useState({})   // symbol → price
  const [equity,     setEquity]     = useState([])
  const [error,      setError]      = useState('')
  const wsRef = useRef(null)

  // ── WebSocket ─────────────────────────────────────────────────────────
  const connectWS = useCallback(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => { setConnected(false); setTimeout(connectWS, 3000) }
    ws.onerror = () => setConnected(false)

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'tick') {
        setTicks(t => ({ ...t, [msg.data.symbol]: msg.data }))
        if (msg.portfolio) {
          setPortfolio(msg.portfolio)
          setEquity(eq => {
            const pt = { t: Date.now(), v: Math.round(msg.portfolio.capital + msg.portfolio.unrealised_pnl) }
            return [...eq.slice(-200), pt]
          })
        }
      }
      if (msg.type === 'signals' && msg.signals?.length) {
        setSignals(prev => {
          const newSigs = msg.signals.map(s => ({ ...s, symbol: msg.symbol, regime: msg.regime, ts: Date.now() }))
          return [...newSigs, ...prev].slice(0, 100)
        })
      }
      if (msg.type === 'trade_opened') {
        if (msg.portfolio) setPortfolio(msg.portfolio)
      }
      if (msg.type === 'trade_closed') {
        if (msg.portfolio) setPortfolio(msg.portfolio)
        if (msg.data) setTrades(t => [msg.data, ...t].slice(0, 100))
      }
    }
  }, [])

  useEffect(() => {
    connectWS()
    getPaperStatus().then(r => setRunning(r.data.running)).catch(() => {})
    return () => wsRef.current?.close()
  }, [])

  // ── Controls ──────────────────────────────────────────────────────────
  const toggle = async () => {
    setError('')
    try {
      if (running) {
        await stopPaper()
        setRunning(false)
        setPortfolio(null)
      } else {
        await startPaper(null)
        setRunning(true)
        // Fetch initial signals + trades
        getPaperSignals().then(r => setSignals(r.data.signals || []))
        getPaperTrades().then(r => setTrades(r.data.trades || []))
      }
    } catch (e) {
      setError(e.response?.data?.detail || String(e))
    }
  }

  const fmt = n => `₹${Number(n || 0).toLocaleString('en-IN')}`
  const pnlColor = n => Number(n) >= 0 ? 'text-green-400' : 'text-red-400'

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-100">Paper Trading</h2>
          <p className="text-gray-500 text-xs mt-0.5">Live simulation on NSE/BSE — no real money at risk</p>
        </div>
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-1.5 text-xs ${connected ? 'text-green-400' : 'text-gray-600'}`}>
            {connected ? <Wifi size={12}/> : <WifiOff size={12}/>}
            {connected ? 'Live' : 'Disconnected'}
          </div>
          <button onClick={toggle}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              running
                ? 'bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20'
                : 'bg-green-500 text-black hover:bg-green-400'
            }`}>
            {running ? <><Square size={13}/> Stop</> : <><Play size={13}/> Start Paper Trading</>}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800/40 rounded-xl p-3 flex items-center gap-2">
          <AlertTriangle size={14} className="text-red-400 shrink-0"/>
          <span className="text-red-400 text-sm">{error}</span>
        </div>
      )}

      {!running && !portfolio && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-10 text-center">
          <Activity size={32} className="mx-auto mb-3 text-gray-700"/>
          <p className="text-gray-500 text-sm">Click Start Paper Trading to begin live simulation</p>
          <p className="text-gray-700 text-xs mt-2">System will scan 12 Nifty50 stocks every 5 minutes and trade on consensus signals</p>
        </div>
      )}

      {(running || portfolio) && (
        <>
          {/* Portfolio metrics */}
          <div className="grid grid-cols-4 gap-3">
            <MCard label="Capital"       value={fmt(portfolio?.capital)}        color="text-gray-100"/>
            <MCard label="Unrealised P&L" value={fmt(portfolio?.unrealised_pnl)} color={pnlColor(portfolio?.unrealised_pnl)} sub="open positions"/>
            <MCard label="Realised P&L"   value={fmt(portfolio?.realised_pnl)}   color={pnlColor(portfolio?.realised_pnl)}   sub="closed trades"/>
            <MCard label="Total P&L"      value={`${portfolio?.total_pnl_pct >= 0 ? '+' : ''}${portfolio?.total_pnl_pct?.toFixed(2) ?? '0.00'}%`}
                   color={pnlColor(portfolio?.total_pnl_pct)} sub={fmt(portfolio?.total_pnl)}/>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Live equity */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-gray-300 text-sm font-semibold">Live Equity</span>
                <span className="text-gray-600 text-xs">{equity.length} data points</span>
              </div>
              {equity.length > 1 ? (
                <ResponsiveContainer width="100%" height={140}>
                  <LineChart data={equity}>
                    <XAxis dataKey="t" hide/>
                    <YAxis tickFormatter={v => `₹${(v/1000).toFixed(0)}K`} tick={{fill:'#6b7280',fontSize:9}} width={50}/>
                    <Tooltip formatter={v => [fmt(v),'Capital']}
                      contentStyle={{background:'#111827',border:'1px solid #374151',borderRadius:'8px',fontSize:'11px'}}/>
                    <ReferenceLine y={500000} stroke="#374151" strokeDasharray="3 3"/>
                    <Line type="monotone" dataKey="v" stroke="#22c55e" dot={false} strokeWidth={2}/>
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-36 flex items-center justify-center text-gray-700 text-xs">
                  Waiting for price updates...
                </div>
              )}
            </div>

            {/* Live tick prices */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <span className="text-gray-300 text-sm font-semibold block mb-3">Live Prices</span>
              <div className="grid grid-cols-2 gap-1.5 overflow-auto max-h-40">
                {Object.entries(ticks).map(([sym, tick]) => (
                  <div key={sym} className="bg-gray-800 rounded-lg px-2.5 py-1.5 flex justify-between items-center">
                    <span className="text-gray-400 text-xs font-medium">{sym}</span>
                    <div className="text-right">
                      <div className="text-gray-200 text-xs font-mono">₹{tick.price?.toFixed(2)}</div>
                      <div className={`text-xs ${tick.change_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {tick.change_pct >= 0 ? '+' : ''}{tick.change_pct?.toFixed(3)}%
                      </div>
                    </div>
                  </div>
                ))}
                {Object.keys(ticks).length === 0 && (
                  <div className="col-span-2 text-gray-700 text-xs text-center py-4">Connecting to feed...</div>
                )}
              </div>
            </div>
          </div>

          {/* Open positions */}
          {portfolio?.positions?.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <span className="text-gray-300 text-sm font-semibold block mb-3">
                Open Positions ({portfolio.positions.length})
              </span>
              <table className="w-full text-xs">
                <thead><tr className="text-gray-600 border-b border-gray-800">
                  {['Symbol','Dir','Qty','Entry','Current','Unreal P&L','SL','Target','Strategy','Conf'].map(h => (
                    <th key={h} className="text-left py-2 pr-3 font-medium">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {portfolio.positions.map((p,i) => (
                    <tr key={i} className="border-b border-gray-800/40 hover:bg-gray-800/20">
                      <td className="py-2 pr-3 font-bold text-gray-100">{p.symbol}</td>
                      <td className={`pr-3 font-bold ${p.direction==='BUY'?'text-green-400':'text-red-400'}`}>{p.direction}</td>
                      <td className="pr-3 text-gray-300">{p.quantity}</td>
                      <td className="pr-3 text-gray-300 font-mono">₹{p.entry?.toFixed(2)}</td>
                      <td className="pr-3 text-gray-200 font-mono">₹{p.current?.toFixed(2)}</td>
                      <td className={`pr-3 font-bold ${p.unrealised_pnl>=0?'text-green-400':'text-red-400'}`}>
                        ₹{p.unrealised_pnl?.toLocaleString('en-IN')}
                      </td>
                      <td className="pr-3 text-red-400 font-mono">₹{p.stop_loss?.toFixed(2)}</td>
                      <td className="pr-3 text-green-400 font-mono">₹{p.target?.toFixed(2)}</td>
                      <td className="pr-3 text-gray-500">{p.strategy}</td>
                      <td className="text-gray-400">{p.confidence?.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Signal feed */}
          {signals.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <span className="text-gray-300 text-sm font-semibold block mb-3">Signal Feed</span>
              <div className="space-y-2 overflow-auto max-h-64">
                {signals.slice(0, 20).map((s, i) => {
                  const c = s.direction === 'BUY' ? 'text-green-400' : 'text-red-400'
                  return (
                    <div key={i} className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-2.5 flex items-center gap-3">
                      <span className="text-gray-200 text-xs font-bold w-20">{s.symbol}</span>
                      <span className={`text-xs font-bold ${c} w-8`}>{s.direction}</span>
                      <span className="text-gray-500 text-xs w-20">{s.strategy}</span>
                      <div className="flex-1"><ConfBar value={s.confidence}/></div>
                      <span className="text-gray-600 text-xs w-12 text-right font-mono">RR {s.rr}x</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Closed trades */}
          {trades.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <span className="text-gray-300 text-sm font-semibold block mb-3">
                Closed Trades ({trades.length})
              </span>
              <div className="overflow-auto max-h-60">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-gray-900">
                    <tr className="text-gray-600 border-b border-gray-800">
                      {['Symbol','Dir','Qty','Entry','Exit','Net P&L','Reason','Conf','Closed'].map(h=>(
                        <th key={h} className="text-left py-2 pr-3 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((t,i)=>(
                      <tr key={i} className="border-b border-gray-800/30 hover:bg-gray-800/20">
                        <td className="py-1.5 pr-3 font-bold text-gray-200">{t.symbol}</td>
                        <td className={`pr-3 font-bold ${t.direction==='BUY'?'text-green-400':'text-red-400'}`}>{t.direction}</td>
                        <td className="pr-3 text-gray-400">{t.quantity}</td>
                        <td className="pr-3 text-gray-400 font-mono">₹{t.entry?.toFixed(2)}</td>
                        <td className="pr-3 text-gray-400 font-mono">₹{t.exit?.toFixed(2)}</td>
                        <td className={`pr-3 font-bold ${t.net_pnl>=0?'text-green-400':'text-red-400'}`}>₹{t.net_pnl?.toLocaleString('en-IN')}</td>
                        <td className="pr-3 text-gray-500">{t.reason}</td>
                        <td className="pr-3 text-gray-500">{t.confidence?.toFixed(1)}%</td>
                        <td className="text-gray-600">{t.closed_at?.slice(11,19)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
