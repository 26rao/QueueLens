import { ArrowRight, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import type { PreviewResponse } from '../../types';

interface ImpactComparisonProps {
  preview: PreviewResponse | null;
  applyLoading: boolean;
  onApply: () => void;
  onCancel: () => void;
}

function MetricRow({ label, before, baseline, after }: { label: string; before: any; baseline?: any; after: any }) {
  const improved = typeof after === 'number' && typeof before === 'number' && after < before;
  const worse = typeof after === 'number' && typeof before === 'number' && after > before;
  return (
    <div className="grid grid-cols-4 gap-2 text-sm py-2 border-b border-gray-50 items-center">
      <div className="text-gray-600 font-medium text-xs">{label}</div>
      <div className="font-mono text-xs text-gray-700">{typeof before === 'number' ? before.toFixed(1) : before}</div>
      <div className="font-mono text-xs text-gray-500">{typeof baseline === 'number' ? baseline.toFixed(1) : (baseline ?? '—')}</div>
      <div className={`font-mono text-xs font-semibold ${improved ? 'text-teal-600' : worse ? 'text-amber-600' : 'text-gray-800'}`}>
        {typeof after === 'number' ? after.toFixed(1) : after}
        {improved && ' (improved)'}{worse && ' (increased)'}
      </div>
    </div>
  );
}

export function ImpactComparison({ preview, applyLoading, onApply, onCancel }: ImpactComparisonProps) {
  if (!preview) return null;

  const { before_metrics: bm, after_metrics: am, baseline_metrics: blm } = preview;

  return (
    <div className="bg-white rounded-xl border border-teal-200 shadow-md">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-teal-50/50 rounded-t-xl">
        <div className="flex items-center gap-2">
          <ArrowRight size={18} className="text-teal-600" />
          <h2 className="font-semibold text-slate-900">Optimization Impact Comparison</h2>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-gray-500">Solver:</span>
          <span className={`px-2.5 py-0.5 rounded-full font-semibold ${
            preview.solver_status === 'OPTIMAL' ? 'bg-teal-100 text-teal-800' :
            preview.solver_status === 'FEASIBLE' ? 'bg-blue-100 text-blue-800' :
            'bg-amber-100 text-amber-800'
          }`}>
            {preview.solver_status}
          </span>
        </div>
      </div>
      <div className="p-5 space-y-4">
        <div className="grid grid-cols-4 gap-2 text-xs font-bold text-gray-500 uppercase tracking-wider pb-2 border-b border-gray-200">
          <div>Metric</div>
          <div>Pre-Disruption</div>
          <div>Baseline (Disrupted)</div>
          <div>QueueLens Optimized</div>
        </div>
        <MetricRow label="Avg Waiting Time (min)" before={bm.avg_wait} baseline={blm?.avg_wait} after={am.avg_wait} />
        <MetricRow label="Max Waiting Time (min)" before={bm.max_wait} baseline={blm?.max_wait} after={am.max_wait} />
        <MetricRow label="Scheduled Patients" before={bm.scheduled_count} baseline={blm?.scheduled_count} after={am.scheduled_count} />
        <MetricRow label="Unscheduled Patients" before={bm.unscheduled_count} baseline={blm?.unscheduled_count} after={am.unscheduled_count} />
        
        {preview.affected_patients && preview.affected_patients.length > 0 && (
          <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
            <strong>Reassignments:</strong> {preview.affected_patients.length} patient(s) will be rescheduled or reassigned to a different doctor/slot.
          </div>
        )}
        {preview.unscheduled_patients && preview.unscheduled_patients.length > 0 && (
          <div className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">
            <strong>Unscheduled:</strong> {preview.unscheduled_patients.length} patient(s) cannot fit in the remaining horizon under current constraints.
          </div>
        )}
        
        <div className="flex items-center gap-3 pt-3">
          <button
            type="button"
            onClick={onApply}
            disabled={applyLoading}
            className="flex items-center gap-2 px-6 py-2.5 bg-teal-600 text-white font-medium text-sm rounded-lg hover:bg-teal-700 disabled:opacity-50 transition-colors shadow-sm"
          >
            {applyLoading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
            Confirm and Apply Schedule
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="flex items-center gap-2 px-4 py-2.5 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <XCircle size={16} />
            Discard Preview
          </button>
        </div>
      </div>
    </div>
  );
}
