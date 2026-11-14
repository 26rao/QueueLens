import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { Metrics } from '../../types';

export function AnalyticsCharts({ metrics }: { metrics: Metrics }) {
  const waitData = Object.entries(metrics.avg_wait_by_priority || {}).map(([priority, wait]) => ({
    priority,
    wait: Number((wait || 0).toFixed(1))
  }));

  const utilData = Object.entries(metrics.doctor_utilization || {}).map(([id, util]) => ({
    name: id,
    util: Number((util || 0).toFixed(1))
  }));

  const COLORS: Record<string, string> = { emergency: '#DC2626', urgent: '#D97706', normal: '#0D9488' };

  return (
    <div id="analytics" className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
        <h3 className="font-semibold text-slate-900 mb-4 text-sm">Avg Wait by Priority (min)</h3>
        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={waitData}>
              <XAxis dataKey="priority" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="wait" radius={[4, 4, 0, 0]}>
                {waitData.map((entry, i) => (
                  <Cell key={i} fill={COLORS[entry.priority] || '#0D9488'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
        <h3 className="font-semibold text-slate-900 mb-4 text-sm">Doctor Utilization (%)</h3>
        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={utilData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="util" fill="#0D9488" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
