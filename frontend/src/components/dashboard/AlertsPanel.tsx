import { Bell, AlertTriangle, UserX, Zap } from 'lucide-react';
import type { Alert } from '../../types';
import { minuteToTime } from '../../lib/utils';

const alertIcons: Record<string, any> = {
  doctor_unavailable: UserX,
  add_emergency: Zap,
  default: AlertTriangle,
};

export function AlertsPanel({ alerts }: { alerts: Alert[] }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
      <div className="p-4 border-b border-gray-100 flex items-center gap-2">
        <Bell size={16} className="text-teal-600" />
        <h2 className="font-semibold text-slate-900">Recent Alerts</h2>
      </div>
      <div className="divide-y divide-gray-50 max-h-64 overflow-y-auto">
        {(!alerts || alerts.length === 0) && (
          <div className="p-4 text-sm text-gray-400 text-center">No alerts yet</div>
        )}
        {alerts?.map((alert, i) => {
          const Icon = alertIcons[alert.type] || alertIcons.default;
          return (
            <div key={i} className="p-3 flex items-start gap-3 hover:bg-gray-50">
              <Icon size={16} className="text-amber-500 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-sm text-slate-700 capitalize">{alert.type.replace('_', ' ')}</div>
                <div className="text-xs text-gray-400">{minuteToTime(alert.minute)}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
