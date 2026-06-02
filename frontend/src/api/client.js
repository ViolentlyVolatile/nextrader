import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// ── System ────────────────────────────────────────────────────────────────
export const getHealth        = ()     => api.get('/health')
export const getConfig        = ()     => api.get('/system/config')

// ── Strategies ────────────────────────────────────────────────────────────
export const getStrategies    = ()     => api.get('/strategies')
export const getUniverse      = ()     => api.get('/universe')

// ── Backtest ──────────────────────────────────────────────────────────────
export const runBacktest      = (data) => api.post('/backtest/run', data)
export const getBacktestList  = ()     => api.get('/backtest/results/list')
export const getBacktestTrades= (id)   => api.get(`/backtest/${id}/trades`)
export const getEquityCurve   = (id)   => api.get(`/backtest/${id}/equity`)

// ── Scanner ───────────────────────────────────────────────────────────────
export const scanSymbol       = (sym, exchange='NSE') => api.get(`/scan/${sym}?exchange=${exchange}`)
export const scanNifty50      = ()     => api.get('/scan/bulk/nifty50')

// ── Paper Trading ─────────────────────────────────────────────────────────
export const startPaper       = (symbols) => api.post('/paper/start', { symbols: symbols || null })
export const stopPaper        = ()     => api.post('/paper/stop')
export const getPaperStatus   = ()     => api.get('/paper/status')
export const getPaperPortfolio= ()     => api.get('/paper/portfolio')
export const getPaperSignals  = (n=50) => api.get(`/paper/signals?limit=${n}`)
export const getPaperTrades   = (n=100)=> api.get(`/paper/trades?limit=${n}`)
export const getPaperEquity   = ()     => api.get('/paper/equity')

// ── Evolution ─────────────────────────────────────────────────────────────
export const getOptimizableStrategies = () => api.get('/evolution/optimize/strategies/available')
export const startOptimize    = (data) => api.post('/evolution/optimize', data)
export const getOptProgress   = (key)  => api.get(`/evolution/optimize/${key}/progress`)
export const getOptResult     = (key)  => api.get(`/evolution/optimize/${key}/result`)
export const getGraveyard     = ()     => api.get('/evolution/graveyard')
