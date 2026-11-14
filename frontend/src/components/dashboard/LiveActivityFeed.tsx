import { Activity, AlertCircle, CheckCircle2, RefreshCw, UserPlus, UserX } from 'lucide-react';
import type { SyntheticEvent, OperatingMode } from '../../types';
import { minuteToTime } from '../../lib/utils';

interface LiveActivityFeedProps {
  events: SyntheticEvent[];
  mode: OperatingMode;
  enabled: boolean;
}

export function LiveActivityFeed({ events, mode, enabled }: LiveActivityFeedProps) {
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'emergency_arrival':
        return <AlertCircle className="w-4 h-4 text-rose-600 animate-pulse" />;
      case 'patient_arrival':
        return <UserPlus className="w-4 h-4 text-blue-600" />;
      case 'consultation_completed':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
      case 'queue_reoptimized':
        return <RefreshCw className="w-4 h-4 text-indigo-600" />;
      case 'doctor_unavailability':
        return <UserX className="w-4 h-4 text-amber-600" />;
      default:
        return <Activity className="w-4 h-4 text-slate-500" />;
    }
  };

  const getEventBadge = (type: string) => {
    switch (type) {
      case 'emergency_arrival':
        return <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">EMERGENCY</span>;
      case 'patient_arrival':
        return <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">ARRIVAL</span>;
      case 'consultation_completed':
        return <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">DONE</span>;
      case 'queue_reoptimized':
        return <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">REOPTIMIZED</span>;
      default:
        return <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">EVENT</span>;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm flex flex-col h-full">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-600" />
          <h2 className="font-semibold text-slate-900 text-sm">Hospital Activity Feed</h2>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              enabled ? 'bg-emerald-500 animate-ping' : 'bg-slate-300'
            }`}
          />
          <span className="text-xs font-medium text-slate-600">
            {enabled ? `${mode === 'replay' ? 'Replay Active' : 'Stream Active'}` : 'Manual Mode'}
          </span>
        </div>
      </div>

      <div className="p-3 divide-y divide-gray-50 overflow-y-auto max-h-[380px] flex-1">
        {events.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            No synthetic hospital events recorded yet.
            <br />
            Switch to <span className="font-medium text-blue-600">Live Synthetic</span> or advance time to see automated events.
          </div>
        ) : (
          events.map((evt) => (
            <div
              key={evt.id}
              className="py-2.5 px-2 flex items-start gap-2.5 hover:bg-slate-50/80 rounded-lg transition-colors"
            >
              <div className="mt-0.5 shrink-0 p-1 rounded-md bg-slate-50 border border-slate-100">
                {getEventIcon(evt.event_type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1 mb-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-[11px] font-semibold text-slate-700">
                      {minuteToTime(evt.simulation_minute)}
                    </span>
                    {getEventBadge(evt.event_type)}
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">
                    +{evt.simulation_minute}m
                  </span>
                </div>
                <p className="text-xs text-slate-600 truncate">{evt.description}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
