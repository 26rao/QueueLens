import { useState } from 'react';
import { RefreshCw, Wifi, WifiOff, Clock, Menu, Zap } from 'lucide-react';
import { minuteToTime } from '../../lib/utils';

interface HeaderProps {
  currentMinute: number;
  wsConnected: boolean;
  onReset: () => void;
  stateVersion: number;
  onToggleSidebar?: () => void;
}

export function Header({ currentMinute, wsConnected, onReset, stateVersion, onToggleSidebar }: HeaderProps) {
  const [resetting, setResetting] = useState(false);

  const handleReset = async () => {
    setResetting(true);
    try {
      await onReset();
    } finally {
      setTimeout(() => setResetting(false), 500);
    }
  };

  return (
    <header className="bg-white border-b border-gray-200 px-4 sm:px-6 py-3.5 flex flex-wrap items-center justify-between gap-3 sticky top-0 z-20 shadow-xs">
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            type="button"
            onClick={onToggleSidebar}
            className="lg:hidden p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
            aria-label="Toggle navigation"
          >
            <Menu size={20} />
          </button>
        )}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-teal-600 rounded-lg flex items-center justify-center text-white font-bold sm:hidden">
            <Zap size={14} />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 leading-tight">QueueLens</h1>
            <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">Hospital Operations Command Center</p>
          </div>
        </div>
      </div>

      <div className="flex items-center flex-wrap gap-2.5 sm:gap-5">
        <div className="flex items-center gap-1.5 text-xs sm:text-sm text-gray-600 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
          <Clock size={15} className="text-teal-600" />
          <span className="font-mono font-bold text-slate-800">{minuteToTime(currentMinute)}</span>
          <span className="text-gray-400 text-xs font-mono ml-1">v{stateVersion}</span>
        </div>

        <div className="flex items-center gap-1.5 text-xs sm:text-sm px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200">
          {wsConnected ? (
            <>
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
              <Wifi size={14} className="text-teal-600" />
              <span className="text-teal-700 font-medium hidden xs:inline">Live Sync</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-red-400" />
              <WifiOff size={14} className="text-red-500" />
              <span className="text-red-600 font-medium hidden xs:inline">Offline</span>
            </>
          )}
        </div>

        <button
          type="button"
          onClick={handleReset}
          disabled={resetting}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs sm:text-sm font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw size={13} className={resetting ? 'animate-spin' : ''} />
          <span>Reset Scenario</span>
        </button>
      </div>
    </header>
  );
}
