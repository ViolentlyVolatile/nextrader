import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getHealth        = ()      => api.get('/health')
export const getConfig        = ()      => api.get('/system/config')
export const getStrategies    = ()      => api.get('/strategies')
export const getUniverse      = ()      => api.get('/universe')
export const runBacktest      = (data)  => api.post('/backtest/run', data)
export const getBacktestList  = ()      => api.get('/backtest/results/list')
export const getBacktestTrades= (id)   => api.get(`/backtest/${id}/trades`)
export const getEquityCurve   = (id)   => api.get(`/backtest/${id}/equity`)
export const scanSymbol       = (sym, exchange='NSE') => api.get(`/scan/${sym}?exchange=${exchange}`)
export const scanNifty50      = ()      => api.get('/scan/bulk/nifty50')
