import { LayoutDashboard, Users, UserCheck, Calendar, BarChart2, Zap } from 'lucide-react';

const navItems = [
  { icon: LayoutDashboard, label: 'Overview', href: '#overview' },
  { icon: Users, label: 'Queue', href: '#queue' },
  { icon: UserCheck, label: 'Doctors', href: '#doctors' },
  { icon: Calendar, label: 'Timeline', href: '#timeline' },
  { icon: BarChart2, label: 'Analytics', href: '#analytics' },
  { icon: Zap, label: 'Disruptions', href: '#disruptions' },
];

export function Sidebar() {
  return (
    <aside className="w-56 bg-slate-900 text-white flex flex-col min-h-screen">
      <div className="p-5 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-teal-500 rounded-lg flex items-center justify-center">
            <Zap size={16} className="text-white" />
          </div>
          <span className="font-bold text-lg">QueueLens</span>
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ icon: Icon, label, href }) => (
          <a
            key={label}
            href={href}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-700 transition-colors text-sm"
          >
            <Icon size={18} />
            {label}
          </a>
        ))}
      </nav>
      <div className="p-4 text-xs text-slate-500 border-t border-slate-700">
        HackGlobal 2026
      </div>
    </aside>
  );
}
