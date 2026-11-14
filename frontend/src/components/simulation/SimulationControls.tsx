import { Pause, Play, ChevronRight } from 'lucide-react';
import { api } from '../../lib/api';
import type { SimulationState } from '../../types';

interface SimulationControlsProps {
  simulation: SimulationState;
  onRefresh: () => void;
}

export function SimulationControls({ simulation, onRefresh }: SimulationControlsProps) {
  const setSpeed = async (speed: number) => {
    try {
      await api.setSpeed(speed);
      onRefresh();
    } catch (e) {
      console.error(e);
    }
  };

  const advance = async () => {
    try {
      await api.advanceSimulation(15);
      onRefresh();
    } catch (e) {
      console.error(e);
    }
  };

  const togglePause = async () => {
    try {
      await api.pauseSimulation();
      onRefresh();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3 bg-white rounded-xl border border-gray-100 shadow-sm p-3.5">
      <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider mr-1">Simulation Clock:</span>
      <button
        type="button"
        onClick={togglePause}
        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
          simulation?.paused
            ? 'bg-amber-100 text-amber-800 hover:bg-amber-200'
            : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
        }`}
      >
        {simulation?.paused ? <Play size={12} /> : <Pause size={12} />}
        {simulation?.paused ? 'Resume' : 'Pause'}
      </button>
      {[1, 5, 15].map(speed => (
        <button
          key={speed}
          type="button"
          onClick={() => setSpeed(speed)}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
            simulation?.speed === speed && !simulation?.paused
              ? 'bg-teal-600 text-white shadow-sm'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          {speed}x
        </button>
      ))}
      <button
        type="button"
        onClick={advance}
        className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors shadow-sm"
      >
        <ChevronRight size={13} />
        +15 Simulated Min
      </button>
      <span className="text-xs font-mono text-gray-500 ml-auto">
        Simulated Minute: <strong className="text-slate-800">{simulation?.current_minute ?? 0}</strong>
      </span>
    </div>
  );
}
