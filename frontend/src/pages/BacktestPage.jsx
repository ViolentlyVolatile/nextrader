import { useState } from 'react'
import { runBacktest, getBacktestTrades, getEquityCurve } from '../api/client'
import {
  ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ReferenceLine, CartesianGrid, Area, AreaChart, Cell
} from 'recharts'
import { Play, Loader2, AlertCircle, TrendingUp, TrendingDown, BarChart2, Activity } from 'lucide-react'

const SYMBOLS = ['RELIANCE','TCS','HDFCBANK','INFY','ICICIBANK','SBIN','BAJFINANCE',
                 'AXISBANK','ITC','WIPRO','MARUTI','TATAMOTORS','KOTAKBANK','LT','ADANIENT']

// ── Custom candlestick bar ────────────────────────────────────────────────────
const CandleBar = (props) => {
  const { x, y, width, height, payload } = props
  if (!payload) return null
  const { open, high, low, close, tradeDir } = payload
  const isGreen  = close >= open
  const color    = tradeDir === 'BUY' ? '#22c55e' : tradeDir === 'SELL' ? '#ef4444' : (isGreen ? '#22c55e' : '#ef4444')
  const bodyTop  = Math.min(y, y + height)
  const bodyH    = Math.max(Math.abs(height), 1)
  return (
    <g>
      {/* Wick */}
      <line x1={x + width/2} y1={props.high} x2={x + width/2} y2={props.low}
            stroke={color} strokeWidth={1} opacity={0.6}/>
      {/* Body */}
      <rect x={x + 1} y={bodyTop} width={Math.max(width - 2, 1)} height={bodyH}
            fill={color} opacity={tradeDir ? 1 : 0.85} rx={1}/>
      {/* Trade marker */}
      {tradeDir && (
        <text x={x + width/2} y={tradeDir === 'BUY' ? props.low - 8 : props.high + 14}
              textAnchor="middle" fontSize={9} fill={color} fontWeight="bold">
          {tradeDir === 'BUY' ? '▲' : '▼'}
        </text>
      )}
    </g>
  )
}

// ── Metric card ───────────────────────────────────────────────────────────────
const Metric = ({ label, value, sub, color = 'text-gray-100' }) => (
  <div className="bg-gray-900/80 border border-gray-800 rounded-lg p-3">
    <div className="text-gray-500 text-xs mb-1 uppercase tracking-wider">{label}</div>
    <div className={`text-lg font-bold font-mono ${color}`}>{value}</div>
    {sub && <div className="text-gray-600 text-xs mt-0.5">{sub}</div>}
  </div>
)

// ── Custom tooltip ────────────────────────────────────────────────────────────
const CandleTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  if (!d) return null
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-xs font-mono shadow-xl">
      <div className="text-gray-400 mb-1.5">{d.date}</div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
        <span className="text-gray-500">O</span><span className="text-gray-200">₹{d.open?.toFixed(2)}</span>
        <span className="text-gray-500">H</span><span className="text-green-400">₹{d.high?.toFixed(2)}</span>
        <span className="text-gray-500">L</span><span className="text-red-400">₹{d.low?.toFixed(2)}</span>
        <span className="text-gray-500">C</span><span className={d.close>=d.open?'text-green-400':'text-red-400'}>₹{d.close?.toFixed(2)}</span>
      </div>
      {d.tradeDir && (
        <div className={`mt-1.5 pt-1.5 border-t border-gray-700 font-bold ${d.tradeDir==='BUY'?'text-green-400':'text-red-400'}`}>
          {d.tradeDir} @ ₹{d.close?.toFixed(2)}
        </div>
      )}
    </div>
  )
}

const EquityTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const v = payload[0]?.value
  const dd = payload[1]?.value
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-xs font-mono shadow-xl">
      <div className="text-gray-200">₹{v?.toLocaleString('en-IN')}</div>
      {dd !== undefined && <div className="text-red-400 mt-0.5">DD: {(dd*100).toFixed(2)}%</div>}
    </div>
  )
}

export default function BacktestPage() {
  const [form, setForm]       = useState({ symbol:'RELIANCE', exchange:'NSE', days:365, starting_capital:500000 })
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [trades,  setTrades]  = useState([])
  const [equity,  setEquity]  = useState([])
  const [ohlcv,   setOhlcv]   = useState([])   // for candlestick chart
  const [error,   setError]   = useState('')
  const [chartTab,setChartTab]= useState('candles')

  const handleRun = async () => {
    setLoading(true); setError(''); setResult(null); setTrades([]); setEquity([]); setOhlcv([])
    try {
      const r   = await runBacktest(form)
      setResult(r.data)

      const [t, e] = await Promise.all([
        getBacktestTrades(r.data.result_id),
        getEquityCurve(r.data.result_id),
      ])

      const tradeList = t.data.trades || []
      setTrades(tradeList)

      // Build equity + drawdown series
      const eq = e.data.equity_curve || []
      const peak = eq.reduce((acc, v, i) => { acc.push(Math.max(v, i > 0 ? acc[i-1] : v)); return acc }, [])
      setEquity(eq.map((v, i) => ({
        i,
        v:  Math.round(v),
        dd: peak[i] > 0 ? (v - peak[i]) / peak[i] : 0
      })))

      // Fetch OHLCV for candlestick (from sample data via scan endpoint)
      try {
        const scanRes = await fetch(`/api/scan/${form.symbol}?exchange=${form.exchange}&days=${form.days}`).then(r=>r.json())
        // We don't get OHLCV from scan — use equity curve bars as proxy for now
      } catch {}

      // Build candlestick data from equity + trade markers
      // Map trades to approximate bar positions
      const tradeMap = {}
      tradeList.forEach(t => {
        // Use entry/exit prices as markers
        if (t.direction) tradeMap[t.entry_price?.toFixed(0)] = t.direction
      })

      // Generate synthetic OHLCV from equity curve (visual representation)
      const syntheticOHLCV = eq.map((capVal, i) => {
        const prev   = i > 0 ? eq[i-1] : capVal
        const change = capVal - prev
        const base   = 100 + (i / eq.length) * 50   // normalised price
        const noise  = (Math.random() - 0.5) * 2
        const o      = base
        const c      = base + change / 5000 + noise
        const h      = Math.max(o, c) + Math.abs(noise) * 0.5
        const lo     = Math.min(o, c) - Math.abs(noise) * 0.5
        // Check if a trade opened near this bar
        const tradeMark = tradeList.find((t, ti) => ti === i) 
        return {
          i, date: `Bar ${i+1}`,
          open: +o.toFixed(2), high: +h.toFixed(2),
          low:  +lo.toFixed(2), close: +c.toFixed(2),
          tradeDir: tradeMark?.direction || null,
          volume: Math.floor(Math.random() * 1000000 + 500000)
        }
      })
      setOhlcv(syntheticOHLCV)

    } catch (e) {
      setError(e.response?.data?.detail || String(e))
    } finally {
      setLoading(false)
    }
  }

  const fmt    = n => `₹${Number(n || 0).toLocaleString('en-IN')}`
  const pColor = n => Number(n) >= 0 ? 'text-green-400' : 'text-red-400'
  const pSign  = n => Number(n) >= 0 ? '+' : ''

  return (
    <div className="space-y-4">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-100">Strategy Backtester</h2>
          <p className="text-gray-500 text-xs mt-0.5">12-strategy consensus · Zerodha brokerage simulation · Kelly position sizing</p>
        </div>
      </div>

      {/* ── Config bar ── */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-wrap gap-4 items-end">
        <div className="flex flex-col gap-1">
          <label className="text-gray-500 text-xs uppercase tracking-wider">Symbol</label>
          <select value={form.symbol} onChange={e=>setForm(f=>({...f,symbol:e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-green-500 min-w-32">
            {SYMBOLS.map(s=><option key={s}>{s}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-gray-500 text-xs uppercase tracking-wider">Exchange</label>
          <select value={form.exchange} onChange={e=>setForm(f=>({...f,exchange:e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-green-500">
            <option>NSE</option><option>BSE</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-gray-500 text-xs uppercase tracking-wider">Period</label>
          <select value={form.days} onChange={e=>setForm(f=>({...f,days:+e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-green-500">
            <option value={180}>6 Months</option>
            <option value={365}>1 Year</option>
            <option value={730}>2 Years</option>
            <option value={1095}>3 Years</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-gray-500 text-xs uppercase tracking-wider">Capital</label>
          <input type="number" value={form.starting_capital}
            onChange={e=>setForm(f=>({...f,starting_capital:+e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-green-500 w-32"/>
        </div>
        <button onClick={handleRun} disabled={loading}
          className="flex items-center gap-2 bg-green-500 hover:bg-green-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-bold px-5 py-2 rounded-lg text-sm transition-all hover:shadow-lg hover:shadow-green-500/20">
          {loading ? <Loader2 size={14} className="animate-spin"/> : <Play size={14}/>}
          {loading ? 'Running...' : 'Run Backtest'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800/40 rounded-xl p-3 flex items-center gap-2">
          <AlertCircle size={14} className="text-red-400 shrink-0"/>
          <span className="text-red-400 text-sm">{error}</span>
        </div>
      )}

      {result && (
        <div className="space-y-4">

          {/* ── Metrics row — TradingView style ── */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-gray-200 font-bold text-sm font-mono">{form.symbol} · NSE · {form.days}d</span>
                <span className={`text-sm font-bold font-mono ${pColor(result.total_pnl)}`}>
                  {pSign(result.total_pnl)}{fmt(result.total_pnl)}
                  <span className="text-xs ml-1">({pSign(result.total_pnl_pct)}{result.total_pnl_pct?.toFixed(2)}%)</span>
                </span>
              </div>
              <div className="flex items-center gap-1 text-xs text-gray-600">
                <span className="w-3 h-3 rounded-sm bg-green-500/60 inline-block"/>BUY
                <span className="w-3 h-3 rounded-sm bg-red-500/60 inline-block ml-2"/>SELL
              </div>
            </div>

            <div className="grid grid-cols-8 gap-2">
              <Metric label="Trades"       value={result.total_trades} />
              <Metric label="Win Rate"     value={`${(result.win_rate*100).toFixed(1)}%`}
                      color={result.win_rate >= 0.5 ? 'text-green-400' : 'text-red-400'} />
              <Metric label="Profit Factor" value={result.profit_factor === Infinity ? '∞' : result.profit_factor?.toFixed(2)}
                      color={result.profit_factor >= 1 ? 'text-green-400' : 'text-red-400'} />
              <Metric label="Sharpe"       value={result.sharpe_ratio?.toFixed(2)}
                      color={result.sharpe_ratio >= 0 ? 'text-green-400' : 'text-red-400'} />
              <Metric label="Max DD"       value={`${(result.max_drawdown_pct*100).toFixed(1)}%`}
                      color="text-red-400" />
              <Metric label="Net P&L"      value={fmt(result.total_pnl)}
                      color={pColor(result.total_pnl)} />
              <Metric label="Return"       value={`${pSign(result.total_pnl_pct)}${result.total_pnl_pct?.toFixed(2)}%`}
                      color={pColor(result.total_pnl_pct)} />
              <Metric label="Final Capital" value={fmt(result.final_capital)}
                      sub={`Started ${fmt(form.starting_capital)}`} />
            </div>
          </div>

          {/* ── Chart panel ── */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            {/* Chart tabs */}
            <div className="flex items-center gap-1 px-4 pt-3 pb-0 border-b border-gray-800">
              {[['candles','Equity + Drawdown', Activity],['trades','Trade P&L', BarChart2]].map(([id,label,Icon])=>(
                <button key={id} onClick={()=>setChartTab(id)}
                  className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-t-lg transition-colors -mb-px ${
                    chartTab===id
                      ? 'bg-gray-800 text-gray-100 border border-gray-700 border-b-gray-800'
                      : 'text-gray-500 hover:text-gray-300'
                  }`}>
                  <Icon size={11}/>{label}
                </button>
              ))}
            </div>

            <div className="p-4">
              {chartTab === 'candles' && equity.length > 1 && (
                <div className="space-y-3">
                  {/* Equity curve */}
                  <div>
                    <div className="text-gray-500 text-xs mb-2 uppercase tracking-wider">Portfolio Value</div>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={equity} margin={{top:4,right:4,left:0,bottom:0}}>
                        <defs>
                          <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#22c55e" stopOpacity={0.3}/>
                            <stop offset="100%" stopColor="#22c55e" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="2 6" stroke="#1f2937" vertical={false}/>
                        <XAxis dataKey="i" hide/>
                        <YAxis tickFormatter={v=>`₹${(v/1000).toFixed(0)}K`}
                               tick={{fill:'#6b7280',fontSize:9}} width={52} axisLine={false} tickLine={false}/>
                        <Tooltip content={<EquityTooltip/>}/>
                        <ReferenceLine y={form.starting_capital} stroke="#374151" strokeDasharray="4 4" strokeWidth={1}/>
                        {/* Trade entry markers */}
                        {trades.map((t,i) => (
                          <ReferenceLine key={i} x={i} stroke={t.direction==='BUY'?'#22c55e':'#ef4444'}
                            strokeWidth={1} strokeDasharray="2 4" strokeOpacity={0.5}/>
                        ))}
                        <Area type="monotone" dataKey="v" stroke="#22c55e" strokeWidth={2}
                              fill="url(#eqGrad)" dot={false}/>
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Drawdown */}
                  <div>
                    <div className="text-gray-500 text-xs mb-2 uppercase tracking-wider">Drawdown</div>
                    <ResponsiveContainer width="100%" height={80}>
                      <AreaChart data={equity} margin={{top:0,right:4,left:0,bottom:0}}>
                        <defs>
                          <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.4}/>
                            <stop offset="100%" stopColor="#ef4444" stopOpacity={0.05}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="2 6" stroke="#1f2937" vertical={false}/>
                        <XAxis dataKey="i" hide/>
                        <YAxis tickFormatter={v=>`${(v*100).toFixed(0)}%`}
                               tick={{fill:'#6b7280',fontSize:9}} width={36} axisLine={false} tickLine={false}/>
                        <ReferenceLine y={0} stroke="#374151" strokeWidth={1}/>
                        <Area type="monotone" dataKey="dd" stroke="#ef4444" strokeWidth={1.5}
                              fill="url(#ddGrad)" dot={false}/>
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {chartTab === 'trades' && trades.length > 0 && (
                <div>
                  <div className="text-gray-500 text-xs mb-3 uppercase tracking-wider">
                    Per-Trade Net P&L — {trades.length} trades
                  </div>
                  <ResponsiveContainer width="100%" height={260}>
                    <ComposedChart data={trades} margin={{top:4,right:4,left:0,bottom:0}}>
                      <CartesianGrid strokeDasharray="2 6" stroke="#1f2937" vertical={false}/>
                      <XAxis dataKey="symbol" hide/>
                      <YAxis tickFormatter={v=>`₹${(v/1000).toFixed(0)}K`}
                             tick={{fill:'#6b7280',fontSize:9}} width={52} axisLine={false} tickLine={false}/>
                      <Tooltip formatter={v=>[fmt(v),'Net P&L']}
                        contentStyle={{background:'#111827',border:'1px solid #374151',borderRadius:'8px',fontSize:'11px'}}/>
                      <ReferenceLine y={0} stroke="#374151" strokeWidth={1}/>
                      <Bar dataKey="net_pnl" radius={[3,3,0,0]} maxBarSize={24}>
                        {trades.map((t,i)=>(
                          <Cell key={i} fill={t.net_pnl>=0?'#22c55e':'#ef4444'} opacity={0.85}/>
                        ))}
                      </Bar>
                      <Line type="monotone"
                        data={trades.map((t,i)=>({...t, cumPnl: trades.slice(0,i+1).reduce((a,b)=>a+b.net_pnl,0)}))}
                        dataKey="cumPnl" stroke="#3b82f6" strokeWidth={2} dot={false} name="Cumulative"/>
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>

          {/* ── Trade log — TradingView style ── */}
          {trades.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
                <span className="text-gray-300 text-sm font-semibold">Trade List</span>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{trades.filter(t=>t.net_pnl>0).length} winners</span>
                  <span className="text-gray-700">·</span>
                  <span>{trades.filter(t=>t.net_pnl<=0).length} losers</span>
                  <span className="text-gray-700">·</span>
                  <span className={pColor(trades.reduce((a,b)=>a+b.net_pnl,0))}>
                    Net {fmt(trades.reduce((a,b)=>a+b.net_pnl,0))}
                  </span>
                </div>
              </div>
              <div className="overflow-auto max-h-72">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-gray-900 border-b border-gray-800">
                    <tr className="text-gray-600">
                      {['#','Dir','Qty','Entry','Exit','Gross','Charges','Net P&L','%','Reason','Conf'].map(h=>(
                        <th key={h} className="text-left py-2.5 px-3 font-medium uppercase tracking-wider text-xs">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((t,i)=>{
                      const pct = ((t.exit_price - t.entry_price) / t.entry_price * 100 * (t.direction==='BUY'?1:-1))
                      const color = t.net_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                      return (
                        <tr key={i} className={`border-b border-gray-800/40 hover:bg-gray-800/30 transition-colors ${
                          i === trades.length-1 ? '' : ''}`}>
                          <td className="py-2 px-3 text-gray-600 font-mono">{i+1}</td>
                          <td className="px-3">
                            <span className={`font-bold px-1.5 py-0.5 rounded text-xs ${
                              t.direction==='BUY'?'bg-green-500/10 text-green-400':'bg-red-500/10 text-red-400'}`}>
                              {t.direction}
                            </span>
                          </td>
                          <td className="px-3 text-gray-400 font-mono">{t.quantity}</td>
                          <td className="px-3 text-gray-300 font-mono">₹{t.entry_price?.toFixed(2)}</td>
                          <td className="px-3 text-gray-300 font-mono">₹{t.exit_price?.toFixed(2)}</td>
                          <td className={`px-3 font-mono ${t.gross_pnl>=0?'text-green-400':'text-red-400'}`}>
                            {t.gross_pnl>=0?'+':''}{fmt(t.gross_pnl)}
                          </td>
                          <td className="px-3 text-gray-600 font-mono">-{fmt(t.brokerage)}</td>
                          <td className={`px-3 font-bold font-mono ${color}`}>
                            {t.net_pnl>=0?'+':''}{fmt(t.net_pnl)}
                          </td>
                          <td className={`px-3 font-mono text-xs ${pct>=0?'text-green-400':'text-red-400'}`}>
                            {pct>=0?'+':''}{pct.toFixed(2)}%
                          </td>
                          <td className="px-3">
                            <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                              t.reason==='TARGET'?'bg-green-500/10 text-green-400':
                              t.reason==='SL'?'bg-red-500/10 text-red-400':'bg-gray-700 text-gray-400'}`}>
                              {t.reason}
                            </span>
                          </td>
                          <td className="px-3 text-gray-500 font-mono">{t.confidence?.toFixed(0)}%</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {/* Summary footer */}
              <div className="px-4 py-2.5 border-t border-gray-800 bg-gray-900/50 flex items-center gap-6 text-xs">
                <span className="text-gray-500">Avg Trade: <span className="text-gray-300 font-mono">
                  {fmt(trades.reduce((a,b)=>a+b.net_pnl,0)/trades.length)}</span></span>
                <span className="text-gray-500">Avg Win: <span className="text-green-400 font-mono">
                  {fmt(trades.filter(t=>t.net_pnl>0).reduce((a,b)=>a+b.net_pnl,0)/(trades.filter(t=>t.net_pnl>0).length||1))}</span></span>
                <span className="text-gray-500">Avg Loss: <span className="text-red-400 font-mono">
                  {fmt(trades.filter(t=>t.net_pnl<=0).reduce((a,b)=>a+b.net_pnl,0)/(trades.filter(t=>t.net_pnl<=0).length||1))}</span></span>
                <span className="text-gray-500">Total Charges: <span className="text-gray-400 font-mono">
                  -{fmt(trades.reduce((a,b)=>a+b.brokerage,0))}</span></span>
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  )
}
