import { Zap, ChevronRight, Loader2 } from 'lucide-react';
import type { DisruptionAction } from '../../types';

const EXAMPLES = [
  'Dr. Rao is unavailable for 60 minutes.',
  'Add two emergency patients.',
  'Dr. Shah is available again.',
  'Dr. Rao and Dr. Sharma are unavailable for 60 minutes. Add two emergency patients.',
];

interface DisruptionPanelProps {
  text: string;
  onTextChange: (t: string) => void;
  onParse: () => void;
  onPreview: () => void;
  parsedActions: DisruptionAction[] | null;
  previewLoading: boolean;
}

export function DisruptionPanel({ text, onTextChange, onParse, onPreview, parsedActions, previewLoading }: DisruptionPanelProps) {
  return (
    <div id="disruptions" className="bg-white rounded-xl border border-gray-100 shadow-sm">
      <div className="p-4 border-b border-gray-100 flex items-center gap-2">
        <Zap size={16} className="text-teal-600" />
        <h2 className="font-semibold text-slate-900">AI Disruption Copilot</h2>
      </div>
      <div className="p-4 space-y-4">
        <textarea
          value={text}
          onChange={e => onTextChange(e.target.value)}
          placeholder="Describe a hospital disruption in natural language..."
          className="w-full h-24 text-sm border border-gray-200 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
        
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onTextChange(ex)}
              className="text-xs px-2.5 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors text-left"
            >
              {ex}
            </button>
          ))}
        </div>
        
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onParse}
            disabled={!text.trim()}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-slate-800 text-white rounded-lg hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight size={14} />
            Parse Disruption
          </button>
          {parsedActions && parsedActions.length > 0 && (
            <button
              type="button"
              onClick={onPreview}
              disabled={previewLoading}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 transition-colors"
            >
              {previewLoading ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
              Preview Schedule Impact
            </button>
          )}
        </div>
        
        {parsedActions && (
          <div className="bg-slate-50 rounded-lg p-3">
            <div className="text-xs font-medium text-gray-500 mb-2">Parsed Structured Actions ({parsedActions.length})</div>
            {parsedActions.length === 0 ? (
              <div className="text-sm text-red-500">No actions recognized. Try a different phrasing or example above.</div>
            ) : (
              <div className="space-y-2">
                {parsedActions.map((action, i) => (
                  <div key={i} className="text-xs bg-white rounded border border-gray-100 p-2 font-mono">
                    <span className="text-teal-600 font-semibold">{action.type}</span>
                    {action.doctor_id && <span className="text-gray-700"> → doctor_id: {action.doctor_id}</span>}
                    {action.duration_minutes && <span className="text-gray-500"> ({action.duration_minutes} min)</span>}
                    {action.count && <span className="text-gray-500"> (count: {action.count})</span>}
                    {action.required_specialty && <span className="text-gray-500"> [specialty: {action.required_specialty}]</span>}
                    {action.appointment_id && <span className="text-gray-500"> [appt: {action.appointment_id}]</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
