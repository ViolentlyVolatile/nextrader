import { LayoutDashboard, FlaskConical, Cpu, Zap, TrendingUp, Activity } from 'lucide-react'

const NAV = [
  { id: 'dashboard',  label: 'Dashboard',   icon: LayoutDashboard },
  { id: 'backtest',   label: 'Backtest',     icon: FlaskConical },
  { id: 'strategies', label: 'Strategies',   icon: Cpu },
  { id: 'scanner',    label: 'Live Scanner', icon: Zap },
]

export default function Sidebar({ page, onNav }) {
  return (
    <aside className="w-52 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center gap-2 mb-1">
          <Activity size={18} className="text-green-400" />
          <h1 className="text-green-400 font-bold tracking-widest text-sm">NEXTRADER</h1>
        </div>
        <p className="text-gray-600 text-xs pl-6">Phase 1 · NSE · BSE · F&O</p>
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {NAV.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => onNav(id)}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
              page === id
                ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                : 'text-gray-500 hover:text-gray-200 hover:bg-gray-800'
            }`}>
            <Icon size={14} />
            {label}
          </button>
        ))}
      </nav>
      <div className="p-3 border-t border-gray-800">
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          <span className="text-gray-600 text-xs">Engine Online</span>
        </div>
      </div>
    </aside>
  )
}
