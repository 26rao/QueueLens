import { Play, Sliders, Sparkles } from 'lucide-react';
import type { OperatingMode } from '../../types';

interface OperatingModeProps {
  currentMode: OperatingMode;
  enabled: boolean;
  onSelectMode: (mode: OperatingMode, enabled?: boolean) => void;
  disabled?: boolean;
}

export function OperatingModeSelector({
  currentMode,
  enabled,
  onSelectMode,
  disabled = false,
}: OperatingModeProps) {
  const modes: { id: OperatingMode; label: string; desc: string; icon: any }[] = [
    {
      id: 'live_synthetic',
      label: 'Live Synthetic',
      desc: 'Autonomous digital twin with arrivals & CP-SAT re-optimization',
      icon: Sparkles,
    },
    {
      id: 'manual',
      label: 'Manual Control',
      desc: 'Admin disruption simulation & AI Copilot',
      icon: Sliders,
    },
    {
      id: 'replay',
      label: 'Judge Replay',
      desc: 'Deterministic scenario: staff outage & emergency surge',
      icon: Play,
    },
  ];

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 bg-slate-50 p-1.5 rounded-xl border border-slate-200">
      <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-2 shrink-0">
        Operating Mode
      </div>
      <div className="flex items-center gap-1 w-full sm:w-auto">
        {modes.map((m) => {
          const Icon = m.icon;
          const isActive = currentMode === m.id && (m.id === 'manual' || enabled);
          return (
            <button
              key={m.id}
              onClick={() => onSelectMode(m.id, m.id !== 'manual')}
              disabled={disabled}
              title={m.desc}
              className={`flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-white text-blue-700 shadow-sm border border-blue-200 ring-1 ring-blue-500/20'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
              <span>{m.label}</span>
              {isActive && (
                <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse ml-0.5" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
