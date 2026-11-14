import { Users, Clock, UserCheck, Calendar, AlertTriangle, Cpu } from 'lucide-react';
import type { Metrics } from '../../types';

interface MetricsCardsProps {
  metrics: Metrics;
  solverStatus?: string;
}

export function MetricsCards({ metrics, solverStatus }: MetricsCardsProps) {
  const cards = [
    { label: 'Patients Waiting', value: metrics.unscheduled_count + (metrics.total_patients - metrics.scheduled_count - metrics.unscheduled_count), icon: Users, color: 'text-amber-600', bg: 'bg-amber-50' },
    { label: 'Avg Wait (min)', value: metrics.avg_wait.toFixed(1), icon: Clock, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Scheduled', value: metrics.scheduled_count, icon: Calendar, color: 'text-teal-600', bg: 'bg-teal-50' },
    { label: 'Unscheduled', value: metrics.unscheduled_count, icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50' },
    { label: 'Total Patients', value: metrics.total_patients, icon: UserCheck, color: 'text-slate-600', bg: 'bg-slate-50' },
    { label: 'Solver Status', value: solverStatus || 'N/A', icon: Cpu, color: 'text-purple-600', bg: 'bg-purple-50' },
  ];

  return (
    <div id="overview" className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map(({ label, value, icon: Icon, color, bg }) => (
        <div key={label} className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <div className={`inline-flex p-2 rounded-lg ${bg} mb-3`}>
            <Icon size={18} className={color} />
          </div>
          <div className="text-2xl font-bold text-slate-900">{value}</div>
          <div className="text-xs text-gray-500 mt-1">{label}</div>
        </div>
      ))}
    </div>
  );
}
