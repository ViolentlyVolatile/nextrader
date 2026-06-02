import { useState } from 'react'
import { runBacktest, getBacktestTrades, getEquityCurve } from '../api/client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Play, Loader2, AlertCircle, TrendingUp, TrendingDown } from 'lucide-react'

const SYMBOLS = ['RELIANCE','TCS','HDFCBANK','INFY','ICICIBANK','SBIN','BAJFINANCE','AXISBANK','ITC','WIPRO']

const Metric = ({ label, value, good }) => {
  const v = parseFloat(value)
  const color = good === undefined ? 'text-blue-400' : (good ? (v >= 0 ? 'text-green-400' : 'text-red-400') : 'text-blue-400')
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-3">
      <div className="text-gray-500 text-xs mb-1">{label}</div>
      <div className={`text-lg font-bold ${color}`}>{value}</div>
    </div>
  )
}

export default function BacktestPage() {
  const [form, setForm]       = useState({ symbol:'RELIANCE', exchange:'NSE', days:365, starting_capital:500000 })
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [trades, setTrades]   = useState([])
  const [equity, setEquity]   = useState([])
  const [error, setError]     = useState('')

  const handleRun = async () => {
    setLoading(true); setError(''); setResult(null); setTrades([]); setEquity([])
    try {
      const r   = await runBacktest(form)
      setResult(r.data)
      const [t,e] = await Promise.all([getBacktestTrades(r.data.result_id), getEquityCurve(r.data.result_id)])
      setTrades(t.data.trades)
      setEquity(e.data.equity_curve.map((v,i) => ({ i, v: Math.round(v) })))
    } catch(e) {
      setError(e.response?.data?.detail || String(e))
    } finally { setLoading(false) }
  }

  const fmt = n => `₹${Number(n).toLocaleString('en-IN')}`
  const pct = n => `${Number(n).toFixed(2)}%`

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-bold text-gray-100 mb-1">Backtesting Engine</h2>
        <p className="text-gray-500 text-xs">Run historical simulations across NSE/BSE with Zerodha brokerage simulation</p>
      </div>

      {/* Form */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-wrap gap-4 items-end">
        <div>
          <label className="text-gray-400 text-xs mb-1 block">Symbol</label>
          <select value={form.symbol} onChange={e=>setForm(f=>({...f,symbol:e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-green-500">
            {SYMBOLS.map(s=><option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="text-gray-400 text-xs mb-1 block">Exchange</label>
          <select value={form.exchange} onChange={e=>setForm(f=>({...f,exchange:e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-green-500">
            <option>NSE</option><option>BSE</option>
          </select>
        </div>
        <div>
          <label className="text-gray-400 text-xs mb-1 block">Lookback (days)</label>
          <select value={form.days} onChange={e=>setForm(f=>({...f,days:+e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-green-500">
            {[180,365,730,1095].map(d=><option key={d} value={d}>{d}d ({Math.round(d/365*10)/10}yr)</option>)}
          </select>
        </div>
        <div>
          <label className="text-gray-400 text-xs mb-1 block">Starting Capital</label>
          <input type="number" value={form.starting_capital} onChange={e=>setForm(f=>({...f,starting_capital:+e.target.value}))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm w-36 focus:outline-none focus:border-green-500" />
        </div>
        <button onClick={handleRun} disabled={loading}
          className="flex items-center gap-2 bg-green-500 hover:bg-green-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-bold px-5 py-2 rounded-lg text-sm transition-colors">
          {loading ? <Loader2 size={15} className="animate-spin" /> : <Play size={15} />}
          {loading ? 'Running...' : 'Run Backtest'}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800/50 rounded-xl p-4 flex items-center gap-3">
          <AlertCircle size={16} className="text-red-400 shrink-0" />
          <span className="text-red-400 text-sm">{error}</span>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          {/* Metrics */}
          <div className="grid grid-cols-4 gap-3">
            <Metric label="Total Trades"   value={result.total_trades}                    />
            <Metric label="Win Rate"       value={pct(result.win_rate*100)}  good={true} />
            <Metric label="Sharpe Ratio"   value={result.sharpe_ratio?.toFixed(2)}  good={true} />
            <Metric label="Max Drawdown"   value={pct(result.max_drawdown_pct*100)} good={false} />
            <Metric label="Profit Factor"  value={result.profit_factor===Infinity?'∞':result.profit_factor?.toFixed(2)} good={true} />
            <Metric label="Total P&L"      value={fmt(result.total_pnl)}  good={true} />
            <Metric label="P&L %"          value={pct(result.total_pnl_pct)} good={true} />
            <Metric label="Final Capital"  value={fmt(result.final_capital)} />
          </div>

          {/* Equity Curve */}
          {equity.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <span className="text-gray-300 text-sm font-semibold">Equity Curve — {result.symbol}</span>
                <span className={`text-xs font-semibold ${result.total_pnl>=0?'text-green-400':'text-red-400'}`}>
                  {result.total_pnl>=0?<TrendingUp size={14} className="inline mr-1"/>:<TrendingDown size={14} className="inline mr-1"/>}
                  {result.total_pnl_pct?.toFixed(2)}% total return
                </span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={equity}>
                  <XAxis dataKey="i" hide />
                  <YAxis tickFormatter={v=>`₹${(v/1000).toFixed(0)}K`} tick={{fill:'#6b7280',fontSize:10}} width={55} />
                  <Tooltip formatter={v=>[`₹${Number(v).toLocaleString('en-IN')}`,'Capital']}
                    contentStyle={{background:'#111827',border:'1px solid #374151',borderRadius:'8px',fontSize:'12px'}} />
                  <ReferenceLine y={form.starting_capital} stroke="#374151" strokeDasharray="4 4" />
                  <Line type="monotone" dataKey="v" stroke="#22c55e" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Trade Log */}
          {trades.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <h3 className="text-gray-300 text-sm font-semibold mb-4">
                Trade Log <span className="text-gray-500 font-normal">({trades.length} trades)</span>
              </h3>
              <div className="overflow-auto max-h-80">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-gray-900">
                    <tr className="text-gray-500 border-b border-gray-800">
                      {['Dir','Qty','Entry','Exit','Gross P&L','Charges','Net P&L','Reason','Confidence'].map(h=>(
                        <th key={h} className="text-left py-2 pr-4 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((t,i) => (
                      <tr key={i} className="border-b border-gray-800/40 hover:bg-gray-800/20 transition-colors">
                        <td className={`py-1.5 pr-4 font-bold ${t.direction==='BUY'?'text-green-400':'text-red-400'}`}>{t.direction}</td>
                        <td className="pr-4 text-gray-300">{t.quantity}</td>
                        <td className="pr-4 text-gray-300">{t.entry_price?.toFixed(2)}</td>
                        <td className="pr-4 text-gray-300">{t.exit_price?.toFixed(2)}</td>
                        <td className={`pr-4 ${t.gross_pnl>=0?'text-green-400':'text-red-400'}`}>₹{t.gross_pnl?.toFixed(0)}</td>
                        <td className="pr-4 text-gray-600">₹{t.brokerage?.toFixed(0)}</td>
                        <td className={`pr-4 font-bold ${t.net_pnl>=0?'text-green-400':'text-red-400'}`}>₹{t.net_pnl?.toFixed(0)}</td>
                        <td className="pr-4 text-gray-400">{t.reason}</td>
                        <td className="text-gray-400">{t.confidence?.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
