import { LayoutDashboard, Users, UserCheck, Calendar, BarChart2, Zap, X } from 'lucide-react';

const navItems = [
  { icon: LayoutDashboard, label: 'Overview', href: '#overview' },
  { icon: Users, label: 'Live Queue', href: '#queue' },
  { icon: UserCheck, label: 'Doctor Availability', href: '#doctors' },
  { icon: Calendar, label: 'Timeline', href: '#timeline' },
  { icon: BarChart2, label: 'Analytics', href: '#analytics' },
  { icon: Zap, label: 'Disruption Copilot', href: '#disruptions' },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const content = (
    <div className="flex flex-col h-full">
      <div className="p-5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-teal-500 rounded-lg flex items-center justify-center text-white shadow-sm">
            <Zap size={18} />
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight text-white block">QueueLens</span>
            <span className="text-[10px] text-teal-400 uppercase font-semibold tracking-wider">Hospital Optimizer</span>
          </div>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="lg:hidden text-slate-400 hover:text-white p-1 rounded-md"
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        )}
      </div>

      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {navItems.map(({ icon: Icon, label, href }) => (
          <a
            key={label}
            href={href}
            onClick={onClose}
            className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-sm font-medium"
          >
            <Icon size={18} className="text-teal-400" />
            {label}
          </a>
        ))}
      </nav>

      <div className="p-4 text-xs text-slate-400 border-t border-slate-800/80 bg-slate-950/40">
        <div className="font-semibold text-slate-300 mb-0.5">HackGlobal 2026</div>
        <div className="text-[11px] text-slate-500">Civic & Real-World Impact</div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden lg:flex w-60 bg-slate-900 text-white flex-col shrink-0 min-h-screen sticky top-0 h-screen border-r border-slate-800">
        {content}
      </aside>

      {/* Mobile Slide-Over Drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs transition-opacity"
            onClick={onClose}
          />
          <div className="relative w-64 max-w-[80vw] bg-slate-900 text-white h-full z-10 shadow-2xl animate-in slide-in-from-left duration-200">
            {content}
          </div>
        </div>
      )}
    </>
  );
}
