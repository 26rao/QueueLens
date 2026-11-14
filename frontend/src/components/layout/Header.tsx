import { RefreshCw, Wifi, WifiOff, Clock } from 'lucide-react';
import { minuteToTime } from '../../lib/utils';

interface HeaderProps {
  currentMinute: number;
  wsConnected: boolean;
  onReset: () => void;
  stateVersion: number;
}

export function Header({ currentMinute, wsConnected, onReset, stateVersion }: HeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">QueueLens</h1>
        <p className="text-sm text-gray-500">Hospital Operations Command Center</p>
      </div>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Clock size={16} />
          <span className="font-mono font-semibold">{minuteToTime(currentMinute)}</span>
          <span className="text-gray-400">v{stateVersion}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          {wsConnected ? (
            <><Wifi size={16} className="text-teal-500" /><span className="text-teal-600">Live</span></>
          ) : (
            <><WifiOff size={16} className="text-red-400" /><span className="text-red-500">Offline</span></>
          )}
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
        >
          <RefreshCw size={14} />
          Reset Scenario
        </button>
      </div>
    </header>
  );
}
