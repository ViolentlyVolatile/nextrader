import { useState } from 'react'
import Sidebar         from './components/Layout/Sidebar'
import DashboardPage   from './pages/DashboardPage'
import BacktestPage    from './pages/BacktestPage'
import StrategiesPage  from './pages/StrategiesPage'
import ScannerPage     from './pages/ScannerPage'
import PaperTradingPage from './pages/PaperTradingPage'
import EvolutionPage   from './pages/EvolutionPage'

const PAGES = {
  dashboard:  DashboardPage,
  backtest:   BacktestPage,
  strategies: StrategiesPage,
  scanner:    ScannerPage,
  paper:      PaperTradingPage,
  evolution:  EvolutionPage,
}

export default function App() {
  const [page, setPage] = useState('dashboard')
  const Page = PAGES[page] || DashboardPage
  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
      <Sidebar page={page} onNav={setPage} />
      <main className="flex-1 overflow-auto p-6">
        <Page />
      </main>
    </div>
  )
}
