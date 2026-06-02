import { useEffect, useState } from 'react'
import { getConfig, getStrategies, getBacktestList } from '../api/client'
import { IndianRupee, ShieldCheck, Layers, TrendingDown, Cpu, Trophy } from 'lucide-react'

const Card = ({ label, value, sub, icon: Icon, color = 'text-green-400' }) => (
  <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors">
    <div className="flex items-center justify-between mb-3">
      <span className="text-gray-500 text-xs font-medium">{label}</span>
      <Icon size={14} className={color} />
    </div>
    <div className={`text-xl font-bold ${color} mb-1`}>{value}</div>
    {sub && <div className="text-gray-600 text-xs">{sub}</div>}
  </div>
)

export default function DashboardPage() {
  const [cfg, setCfg]       = useState(null)
  const [strats, setStrats] = useState([])
  const [results, setResults] = useState([])

  useEffect(() => {
    getConfig().then(r => setCfg(r.data))
    getStrategies().then(r => setStrats(r.data.strategies))
    getBacktestList().then(r => setResults(r.data.results)).catch(()=>{})
  }, [])

  const fmt = n => n ? `₹${Number(n).toLocaleString('en-IN')}` : '—'
  const best = results.sort((a,b)=>(b.total_pnl||0)-(a.total_pnl||0))[0]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-gray-100 mb-1">System Overview</h2>
        <p className="text-gray-500 text-xs">NEXTRADER Phase 1 · {strats.length} strategies active</p>
      </div>

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        <Card label="Starting Capital"  value={cfg ? fmt(cfg.starting_capital) : '—'}    sub="Paper trading capital"   icon={IndianRupee}   color="text-green-400" />
        <Card label="Max Risk / Trade"  value={cfg ? fmt(cfg.max_risk_per_trade) : '—'}  sub="1% per position"         icon={ShieldCheck}   color="text-yellow-400" />
        <Card label="Max Positions"     value={cfg?.max_open_positions ?? '—'}            sub="Simultaneous open trades" icon={Layers}        color="text-blue-400" />
        <Card label="Daily Loss Limit"  value={cfg ? fmt(cfg.daily_loss_limit) : '—'}    sub="3% → system halts"       icon={TrendingDown}  color="text-red-400" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-4">
            <Cpu size={14} className="text-purple-400" />
            <span className="text-gray-300 text-sm font-semibold">Active Strategies ({strats.length})</span>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            {strats.map(s => (
              <div key={s.name} className="bg-gray-800 rounded-lg px-2.5 py-1.5 flex items-center justify-between">
                <span className="text-gray-300 text-xs">{s.name}</span>
                <span className="text-xs text-green-400 ml-2">●</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-4">
            <Trophy size={14} className="text-yellow-400" />
            <span className="text-gray-300 text-sm font-semibold">Recent Backtests</span>
          </div>
          {results.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-gray-600 text-xs">No backtests yet.</p>
              <p className="text-gray-700 text-xs mt-1">Run one in the Backtest tab.</p>
            </div>
          ) : results.slice(0,5).map((r,i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
              <span className="text-gray-300 text-xs font-medium">{r.symbol}</span>
              <div className="flex items-center gap-3 text-xs">
                <span className="text-gray-500">{(r.win_rate*100).toFixed(0)}% WR</span>
                <span className={r.total_pnl>=0?'text-green-400':'text-red-400'}>
                  {r.total_pnl>=0?'+':''}{fmt(r.total_pnl)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Confidence Score Formula */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <p className="text-gray-500 text-xs font-medium mb-3 uppercase tracking-wider">Confidence Score Formula</p>
        <div className="grid grid-cols-4 gap-2">
          {[['Indicator Agreement','35%','text-blue-400'],['Win Rate History','30%','text-green-400'],
            ['Volume Confirmation','20%','text-yellow-400'],['Regime Fit','15%','text-purple-400']].map(([l,p,c])=>(
            <div key={l} className="bg-gray-800 rounded-lg p-3 text-center">
              <div className={`text-xl font-bold ${c} mb-1`}>{p}</div>
              <div className="text-gray-500 text-xs">{l}</div>
            </div>
          ))}
        </div>
        <p className="text-gray-600 text-xs mt-3 text-center">Signals fire only when confidence ≥ 60% · Consensus requires ≥3 strategies agreeing at ≥65%</p>
      </div>
    </div>
  )
}
