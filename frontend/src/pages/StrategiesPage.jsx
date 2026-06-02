import { useEffect, useState } from 'react'
import { getStrategies } from '../api/client'
import { Cpu, Settings, CheckCircle } from 'lucide-react'

const DESCRIPTIONS = {
  MomentumRSI:    'RSI oversold/overbought + Rate of Change momentum confirmation',
  VWAPReversion:  'Mean reversion to VWAP — deviation threshold based entry',
  EMACrossover:   '9/21 EMA crossover with volume confirmation filter',
  SupertrendADX:  'Supertrend flip confirmed by ADX directional strength',
  BollingerSqueeze: 'Bollinger Band squeeze release — volatility breakout',
  PriceAction:    'Engulfing candles, pin bars, inside bars pattern recognition',
  ORB:            'Opening Range Breakout with 15-min range and volume surge',
  MACDDivergence: 'MACD histogram divergence vs price action',
  StochasticSwing:'Stochastic crossover in oversold/overbought zones',
  Ichimoku:       'Ichimoku TK cross above/below cloud — trend confirmation',
  ParabolicSAR:   'SAR flip confirmed by 50 EMA trend direction',
  VolumePOC:      'Volume Profile Point of Control breakout with surge',
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState([])
  useEffect(() => { getStrategies().then(r => setStrategies(r.data.strategies)) }, [])

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-bold text-gray-100 mb-1">Strategy Pool</h2>
        <p className="text-gray-500 text-xs">
          {strategies.length} independent algo agents running in parallel — signals consensus-voted before execution
        </p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-2">
        <p className="text-gray-400 text-xs leading-relaxed">
          Each strategy independently analyzes OHLCV data and emits a signal with a <span className="text-green-400">confidence score (0–100%)</span>.
          Signals below <span className="text-yellow-400">60%</span> are discarded.
          A trade only executes when <span className="text-blue-400">≥3 strategies agree</span> with average confidence <span className="text-blue-400">≥65%</span> — this is the consensus layer.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {strategies.map(s => (
          <div key={s.name} className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Cpu size={13} className="text-purple-400" />
                <span className="text-gray-100 font-semibold text-sm">{s.name}</span>
              </div>
              <div className="flex items-center gap-1 text-xs text-green-400">
                <CheckCircle size={11} />
                <span>Active</span>
              </div>
            </div>
            <p className="text-gray-500 text-xs mb-3 leading-relaxed">{DESCRIPTIONS[s.name] || 'Multi-indicator strategy'}</p>
            {Object.keys(s.params).length > 0 && (
              <div className="border-t border-gray-800 pt-2 mt-2">
                <div className="flex items-center gap-1 mb-1.5">
                  <Settings size={10} className="text-gray-600" />
                  <span className="text-gray-600 text-xs">Parameters</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(s.params).map(([k,v]) => (
                    <span key={k} className="bg-gray-800 text-gray-400 text-xs px-2 py-0.5 rounded font-mono">
                      {k}={String(v)}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
