import { LayoutDashboard, FlaskConical, Cpu, Zap, LineChart, Dna } from 'lucide-react'

const NAV = [
  { id: 'dashboard',  label: 'Dashboard',      icon: LayoutDashboard },
  { id: 'backtest',   label: 'Backtest',        icon: FlaskConical },
  { id: 'strategies', label: 'Strategies',      icon: Cpu },
  { id: 'scanner',    label: 'Live Scanner',    icon: Zap },
  { id: 'paper',      label: 'Paper Trading',   icon: LineChart },
  { id: 'evolution',  label: 'Evolution',       icon: Dna },
]

export default function Sidebar({ page, onNav }) {
  return (
    <aside className="w-52 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"/>
          <h1 className="text-green-400 font-bold tracking-widest text-sm font-mono">NEXTRADER</h1>
        </div>
        <p className="text-gray-600 text-xs pl-4">v2.0 · NSE · BSE · F&O</p>
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {NAV.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => onNav(id)}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
              page === id
                ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                : 'text-gray-500 hover:text-gray-200 hover:bg-gray-800 border border-transparent'
            }`}>
            <Icon size={13} />
            {label}
            {id === 'paper' && <span className="ml-auto text-xs bg-blue-500/20 text-blue-400 px-1 rounded">P2</span>}
            {id === 'evolution' && <span className="ml-auto text-xs bg-purple-500/20 text-purple-400 px-1 rounded">P3</span>}
          </button>
        ))}
      </nav>
      <div className="p-3 border-t border-gray-800">
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"/>
          <span className="text-gray-600 text-xs font-mono">ENGINE ONLINE</span>
        </div>
      </div>
    </aside>
  )
}
