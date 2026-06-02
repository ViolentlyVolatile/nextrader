import { useState, useEffect, useRef } from 'react'
import { startOptimize, getOptProgress, getOptResult, getGraveyard, getOptimizableStrategies } from '../api/client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Dna, Play, Loader2, CheckCircle, XCircle, Eye, AlertTriangle, TrendingUp } from 'lucide-react'

const STATUS_STYLES = {
  active:    'bg-green-500/10 text-green-400 border-green-500/20',
  promoted:  'bg-blue-500/10 text-blue-400 border-blue-500/20',
  watch:     'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  suspended: 'bg-red-500/10 text-red-400 border-red-500/20',
}

export default function EvolutionPage() {
  const [strategies,   setStrategies]   = useState([])
  const [selected,     setSelected]     = useState('')
  const [symbol,       setSymbol]       = useState('RELIANCE')
  const [generations,  setGenerations]  = useState(8)
  const [population,   setPopulation]   = useState(12)
  const [loading,      setLoading]      = useState(false)
  const [progress,     setProgress]     = useState(null)
  const [result,       setResult]       = useState(null)
  const [graveyard,    setGraveyard]    = useState(null)
  const [error,        setError]        = useState('')
  const [activeTab,    setActiveTab]    = useState('optimizer')
  const pollRef = useRef(null)

  useEffect(() => {
    getOptimizableStrategies()
      .then(r => { setStrategies(r.data.strategies); setSelected(r.data.strategies[0] || '') })
      .catch(() => {})
    fetchGraveyard()
    return () => clearInterval(pollRef.current)
  }, [])

  const fetchGraveyard = () => {
    getGraveyard().then(r => setGraveyard(r.data)).catch(() => {})
  }

  const runOpt = async () => {
    setError(''); setResult(null); setProgress(null); setLoading(true)
    try {
      const r   = await startOptimize({ strategy_name: selected, symbol, days: 365, population, generations })
      const key = r.data.key
      pollRef.current = setInterval(async () => {
        const prog = await getOptProgress(key)
        setProgress(prog.data)
        if (prog.data.status === 'complete') {
          clearInterval(pollRef.current)
          const res = await getOptResult(key)
          setResult(res.data)
          setLoading(false)
        }
      }, 2000)
    } catch (e) {
      setError(e.response?.data?.detail || e.response?.data?.error || String(e))
      setLoading(false)
    }
  }

  const SYMBOLS = ['RELIANCE','TCS','HDFCBANK','INFY','ICICIBANK','SBIN','BAJFINANCE','MARUTI']

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-gray-100">Evolutionary Optimizer</h2>
        <p className="text-gray-500 text-xs mt-0.5">Phase 3 — Genetic algorithm to evolve strategy parameters + strategy graveyard</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit">
        {['optimizer','graveyard'].map(t => (
          <button key={t} onClick={() => { setActiveTab(t); if(t==='graveyard') fetchGraveyard() }}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
              activeTab===t ? 'bg-gray-800 text-gray-100' : 'text-gray-500 hover:text-gray-300'
            }`}>{t}</button>
        ))}
      </div>

      {/* ── OPTIMIZER TAB ── */}
      {activeTab === 'optimizer' && (
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-gray-500 text-xs uppercase tracking-widest mb-4">Configuration</div>
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex flex-col gap-1">
                <label className="text-gray-500 text-xs">Strategy</label>
                <select value={selected} onChange={e=>setSelected(e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-purple-500">
                  {strategies.map(s => <option key={s}>{s}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-gray-500 text-xs">Symbol</label>
                <select value={symbol} onChange={e=>setSymbol(e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-purple-500">
                  {SYMBOLS.map(s=><option key={s}>{s}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-gray-500 text-xs">Generations</label>
                <select value={generations} onChange={e=>setGenerations(+e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-purple-500">
                  {[4,6,8,10,15].map(n=><option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-gray-500 text-xs">Population</label>
                <select value={population} onChange={e=>setPopulation(+e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-purple-500">
                  {[8,12,16,20].map(n=><option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <button onClick={runOpt} disabled={loading || !selected}
                className="flex items-center gap-2 bg-purple-500 hover:bg-purple-400 disabled:opacity-50 text-white font-bold px-5 py-2 rounded-lg text-sm transition-colors">
                {loading ? <Loader2 size={14} className="animate-spin"/> : <Dna size={14}/>}
                {loading ? 'Evolving...' : 'Run Evolution'}
              </button>
              {loading && <p className="text-gray-500 text-xs self-center">~{generations * population * 2}s estimated</p>}
            </div>
          </div>

          {error && (
            <div className="bg-red-900/20 border border-red-800/40 rounded-xl p-3 flex items-center gap-2">
              <AlertTriangle size={14} className="text-red-400 shrink-0"/>
              <span className="text-red-400 text-sm">{error}</span>
            </div>
          )}

          {/* Progress */}
          {progress && progress.status === 'running' && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-gray-300 text-sm font-semibold">Evolution Progress</span>
                <span className="text-purple-400 text-xs">Gen {progress.generation}/{progress.total}</span>
              </div>
              <div className="bg-gray-800 rounded-full h-2 mb-2">
                <div className="bg-purple-500 h-2 rounded-full transition-all"
                  style={{width:`${(progress.generation/progress.total)*100}%`}}/>
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>Best fitness so far: <span className="text-purple-400 font-bold">{progress.best_fitness?.toFixed(1)}%</span></span>
                <span className="text-gray-600">Evaluating {population} individuals per generation</span>
              </div>
            </div>
          )}

          {/* Results */}
          {result && result.status === 'complete' && (
            <div className="space-y-4">
              <div className="bg-gray-900 border border-purple-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle size={16} className="text-purple-400"/>
                  <span className="text-gray-200 font-semibold">{result.strategy} — Best Parameters Found</span>
                  <span className="ml-auto text-purple-400 font-bold text-sm">Fitness: {result.best_fitness?.toFixed(1)}%</span>
                </div>
                <div className="grid grid-cols-4 gap-2">
                  {Object.entries(result.best_params || {}).map(([k,v]) => (
                    <div key={k} className="bg-gray-800 rounded-lg px-3 py-2">
                      <div className="text-gray-600 text-xs mb-1">{k}</div>
                      <div className="text-purple-400 font-bold font-mono">{String(v)}</div>
                    </div>
                  ))}
                </div>
              </div>

              {result.generations?.length > 0 && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <span className="text-gray-300 text-sm font-semibold block mb-4">Fitness by Generation</span>
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={result.generations}>
                      <XAxis dataKey="generation" tick={{fill:'#6b7280',fontSize:10}} label={{value:'Gen',position:'insideRight',fill:'#6b7280',fontSize:10}}/>
                      <YAxis tick={{fill:'#6b7280',fontSize:10}} domain={[0,100]}/>
                      <Tooltip contentStyle={{background:'#111827',border:'1px solid #374151',borderRadius:'8px',fontSize:'11px'}}/>
                      <Line type="monotone" dataKey="best_fitness" stroke="#a855f7" strokeWidth={2} dot={false} name="Best"/>
                      <Line type="monotone" dataKey="avg_fitness"  stroke="#6b7280" strokeWidth={1} dot={false} name="Avg"/>
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── GRAVEYARD TAB ── */}
      {activeTab === 'graveyard' && graveyard && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-4 gap-3">
            {[
              ['Active',    graveyard.summary?.active,    'text-green-400'],
              ['Promoted',  graveyard.summary?.promoted,  'text-blue-400'],
              ['Watch',     graveyard.summary?.watch,     'text-yellow-400'],
              ['Suspended', graveyard.summary?.suspended, 'text-red-400'],
            ].map(([l,v,c]) => (
              <div key={l} className="bg-gray-900 border border-gray-800 rounded-xl p-3">
                <div className="text-gray-500 text-xs mb-1">{l}</div>
                <div className={`text-2xl font-bold font-mono ${c}`}>{v ?? 0}</div>
              </div>
            ))}
          </div>

          {/* Strategy cards */}
          <div className="grid grid-cols-2 gap-3">
            {(graveyard.strategies || []).map((s, i) => (
              <div key={i} className={`bg-gray-900 border rounded-xl p-4 ${
                s.status === 'suspended' ? 'border-red-800/40 opacity-60' :
                s.status === 'promoted'  ? 'border-blue-500/30' :
                s.status === 'watch'     ? 'border-yellow-500/30' : 'border-gray-800'
              }`}>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-gray-200 font-semibold text-sm">{s.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded border ${STATUS_STYLES[s.status] || STATUS_STYLES.active}`}>
                    {s.status.toUpperCase()}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs mb-2">
                  <div className="bg-gray-800 rounded p-2 text-center">
                    <div className="text-gray-600 mb-0.5">Trades</div>
                    <div className="text-gray-200 font-bold">{s.total_trades}</div>
                  </div>
                  <div className="bg-gray-800 rounded p-2 text-center">
                    <div className="text-gray-600 mb-0.5">Win Rate</div>
                    <div className={`font-bold ${s.win_rate >= 0.55 ? 'text-green-400' : s.win_rate >= 0.42 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {(s.win_rate * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="bg-gray-800 rounded p-2 text-center">
                    <div className="text-gray-600 mb-0.5">Sharpe</div>
                    <div className={`font-bold ${s.sharpe >= 0 ? 'text-green-400' : 'text-red-400'}`}>{s.sharpe?.toFixed(2)}</div>
                  </div>
                </div>
                <div className="text-gray-600 text-xs">{s.status_reason}</div>
                {s.total_trades > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    Avg conf: {s.avg_confidence}% · PF: {s.profit_factor === Infinity ? '∞' : s.profit_factor?.toFixed(2)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
