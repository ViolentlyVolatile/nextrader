import { useState } from 'react'
import { scanSymbol, scanNifty50 } from '../api/client'
import { Zap, Loader2, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react'

const SYMBOLS = ['RELIANCE','TCS','HDFCBANK','INFY','ICICIBANK','SBIN','BAJFINANCE','AXISBANK','ITC','WIPRO',
                 'KOTAKBANK','LT','HCLTECH','MARUTI','TATAMOTORS','SUNPHARMA','TITAN','NTPC','TECHM','JSWSTEEL']

const ConfBar = ({ value }) => (
  <div className="flex items-center gap-2">
    <div className="flex-1 bg-gray-800 rounded-full h-1.5">
      <div className={`h-1.5 rounded-full transition-all ${value>=70?'bg-green-400':value>=60?'bg-yellow-400':'bg-red-400'}`}
        style={{width:`${value}%`}} />
    </div>
    <span className={`text-xs font-bold w-10 text-right ${value>=70?'text-green-400':value>=60?'text-yellow-400':'text-red-400'}`}>
      {value?.toFixed(1)}%
    </span>
  </div>
)

const SignalCard = ({ sig }) => (
  <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-3 mb-2">
    <div className="flex items-center justify-between mb-2">
      <span className="text-gray-300 text-xs font-semibold">{sig.strategy}</span>
      <div className={`flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded ${sig.direction==='BUY'?'bg-green-500/10 text-green-400':'bg-red-500/10 text-red-400'}`}>
        {sig.direction==='BUY'?<TrendingUp size={10}/>:<TrendingDown size={10}/>}
        {sig.direction}
      </div>
    </div>
    <ConfBar value={sig.confidence} />
    <div className="grid grid-cols-3 gap-1 mt-2 text-xs text-gray-500">
      <span>Entry: <span className="text-gray-300">₹{sig.entry?.toFixed(1)}</span></span>
      <span>SL: <span className="text-red-400">₹{sig.sl?.toFixed(1)}</span></span>
      <span>Tgt: <span className="text-green-400">₹{sig.target?.toFixed(1)}</span></span>
    </div>
    <div className="text-gray-600 text-xs mt-1">RR: {sig.rr}x</div>
  </div>
)

export default function ScannerPage() {
  const [symbol, setSymbol]       = useState('RELIANCE')
  const [loading, setLoading]     = useState(false)
  const [scanning, setScanning]   = useState(false)
  const [result, setResult]       = useState(null)
  const [bulkRes, setBulkRes]     = useState(null)
  const [error, setError]         = useState('')

  const scan = async () => {
    setLoading(true); setError(''); setResult(null)
    try { const r=await scanSymbol(symbol); setResult(r.data) }
    catch(e) { setError(e.response?.data?.detail||String(e)) }
    finally { setLoading(false) }
  }

  const scanAll = async () => {
    setScanning(true); setError(''); setBulkRes(null)
    try { const r=await scanNifty50(); setBulkRes(r.data) }
    catch(e) { setError(e.response?.data?.detail||String(e)) }
    finally { setScanning(false) }
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-bold text-gray-100 mb-1">Live Scanner</h2>
        <p className="text-gray-500 text-xs">Run all 12 strategies on any symbol and see signals with confidence scores</p>
      </div>

      {/* Single scan */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex gap-3 items-end">
        <div>
          <label className="text-gray-400 text-xs mb-1 block">Symbol</label>
          <select value={symbol} onChange={e=>setSymbol(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 text-sm focus:outline-none focus:border-green-500">
            {SYMBOLS.map(s=><option key={s}>{s}</option>)}
          </select>
        </div>
        <button onClick={scan} disabled={loading}
          className="flex items-center gap-2 bg-green-500 hover:bg-green-400 disabled:opacity-50 text-black font-bold px-4 py-2 rounded-lg text-sm">
          {loading?<Loader2 size={14} className="animate-spin"/>:<Zap size={14}/>}
          Scan Symbol
        </button>
        <button onClick={scanAll} disabled={scanning}
          className="flex items-center gap-2 bg-blue-500 hover:bg-blue-400 disabled:opacity-50 text-white font-bold px-4 py-2 rounded-lg text-sm">
          {scanning?<Loader2 size={14} className="animate-spin"/>:<Zap size={14}/>}
          Scan Nifty50 Top 10
        </button>
        {scanning && <span className="text-gray-500 text-xs">This takes ~30s — fetching data for 10 stocks...</span>}
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800/50 rounded-xl p-3 flex items-center gap-2">
          <AlertTriangle size={14} className="text-red-400 shrink-0"/>
          <span className="text-red-400 text-sm">{error}</span>
        </div>
      )}

      {/* Single result */}
      {result && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <span className="text-gray-100 font-bold">{result.symbol}</span>
                <span className="text-gray-500 text-xs ml-2">Regime: </span>
                <span className={`text-xs font-semibold ${result.regime==='TRENDING'?'text-green-400':result.regime==='VOLATILE'?'text-red-400':'text-yellow-400'}`}>
                  {result.regime}
                </span>
              </div>
              <span className="text-gray-500 text-xs">{result.signals?.length} signals</span>
            </div>
            {result.signals?.length===0 ? (
              <p className="text-gray-600 text-xs text-center py-4">No signals above 60% confidence threshold</p>
            ) : result.signals?.map((s,i) => <SignalCard key={i} sig={s} />)}
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-gray-300 text-sm font-semibold mb-4">Consensus</h3>
            {!result.consensus ? (
              <div className="text-center py-8">
                <p className="text-gray-600 text-sm">No consensus</p>
                <p className="text-gray-700 text-xs mt-1">Need ≥3 strategies agreeing at ≥65% confidence</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className={`text-center p-4 rounded-xl border ${result.consensus.direction==='BUY'?'bg-green-500/5 border-green-500/20':'bg-red-500/5 border-red-500/20'}`}>
                  <div className={`text-3xl font-bold mb-1 ${result.consensus.direction==='BUY'?'text-green-400':'text-red-400'}`}>
                    {result.consensus.direction}
                  </div>
                  <div className="text-gray-400 text-xs">{result.consensus.agreeing}/{result.consensus.total} strategies agree</div>
                </div>
                <ConfBar value={result.consensus.avg_confidence} />
                <div className="grid grid-cols-3 gap-2 text-xs">
                  {[['Entry',`₹${result.consensus.entry?.toFixed(2)}`],
                    ['Stop Loss',`₹${result.consensus.sl?.toFixed(2)}`],
                    ['Target',`₹${result.consensus.target?.toFixed(2)}`]].map(([l,v])=>(
                    <div key={l} className="bg-gray-800 rounded p-2 text-center">
                      <div className="text-gray-500 text-xs mb-0.5">{l}</div>
                      <div className="text-gray-200 font-semibold">{v}</div>
                    </div>
                  ))}
                </div>
                <div className="bg-gray-800 rounded p-2 text-center">
                  <span className="text-gray-500 text-xs">Risk : Reward = </span>
                  <span className="text-blue-400 font-bold">1 : {result.consensus.rr}</span>
                </div>
                <div className="space-y-1">
                  {result.consensus.strategies?.map((s,i)=>(
                    <div key={i} className="flex justify-between items-center text-xs">
                      <span className="text-gray-400">{s.name}</span>
                      <ConfBar value={s.confidence} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Bulk scan results */}
      {bulkRes && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h3 className="text-gray-300 text-sm font-semibold mb-1">
            Nifty50 Scan Results
            <span className="text-gray-500 font-normal ml-2">
              {bulkRes.with_signals}/{bulkRes.scanned} stocks with signals
            </span>
          </h3>
          {bulkRes.results?.length===0 ? (
            <p className="text-gray-600 text-sm text-center py-4">No signals found across the universe</p>
          ) : bulkRes.results?.map((r,i) => (
            <div key={i} className="border-b border-gray-800 py-3 last:border-0">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-gray-100 font-semibold text-sm">{r.symbol}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${r.regime==='TRENDING'?'bg-green-500/10 text-green-400':r.regime==='VOLATILE'?'bg-red-500/10 text-red-400':'bg-yellow-500/10 text-yellow-400'}`}>
                    {r.regime}
                  </span>
                  <span className="text-gray-600 text-xs">{r.signals?.length} signals</span>
                </div>
                {r.consensus && (
                  <div className={`text-xs font-bold px-2 py-0.5 rounded ${r.consensus.direction==='BUY'?'bg-green-500/10 text-green-400':'bg-red-500/10 text-red-400'}`}>
                    CONSENSUS {r.consensus.direction} @ {r.consensus.avg_confidence?.toFixed(1)}%
                  </div>
                )}
              </div>
              {r.signals?.slice(0,3).map((s,j)=>(
                <div key={j} className="flex items-center justify-between text-xs text-gray-500 py-0.5">
                  <span>{s.strategy}</span>
                  <div className="flex items-center gap-3">
                    <span className={s.direction==='BUY'?'text-green-400':'text-red-400'}>{s.direction}</span>
                    <span className="text-gray-400">{s.confidence?.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
