import { useQueueState } from './hooks/useQueueState';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { MetricsCards } from './components/dashboard/MetricsCards';
import { QueueTable } from './components/dashboard/QueueTable';
import { DoctorStatus } from './components/dashboard/DoctorStatus';
import { ScheduleTimeline } from './components/dashboard/ScheduleTimeline';
import { AlertsPanel } from './components/dashboard/AlertsPanel';
import { AnalyticsCharts } from './components/dashboard/AnalyticsCharts';
import { DisruptionPanel } from './components/disruption/DisruptionPanel';
import { ImpactComparison } from './components/disruption/ImpactComparison';
import { SimulationControls } from './components/simulation/SimulationControls';
import { Loader2 } from 'lucide-react';

export default function App() {
  const q = useQueueState();

  if (q.loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <Loader2 size={36} className="animate-spin text-teal-600" />
          <p className="text-slate-600 font-medium">Loading QueueLens Dashboard...</p>
        </div>
      </div>
    );
  }

  if (!q.state) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 p-6">
        <div className="text-center max-w-md bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
          <div className="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4 font-bold text-xl">
            !
          </div>
          <h2 className="text-lg font-bold text-slate-800 mb-2">Backend Connection Required</h2>
          <p className="text-slate-500 text-sm mb-6">
            {q.error || 'Could not connect to the QueueLens FastAPI backend at /api/state.'}
          </p>
          <button
            type="button"
            onClick={q.fetchState}
            className="px-5 py-2.5 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 transition-colors shadow-sm"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const { state } = q;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          currentMinute={state.simulation?.current_minute ?? 0}
          wsConnected={q.wsConnected}
          onReset={q.reset}
          stateVersion={state.state_version}
        />
        <main className="flex-1 p-6 space-y-6 overflow-y-auto max-w-[1600px] w-full mx-auto">
          {q.error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-3 text-sm flex items-center justify-between">
              <span>{q.error}</span>
              <button type="button" onClick={q.fetchState} className="underline text-xs ml-4">Dismiss</button>
            </div>
          )}
          
          <SimulationControls simulation={state.simulation} onRefresh={q.fetchState} />
          
          <MetricsCards metrics={state.metrics} solverStatus={q.preview?.solver_status} />
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <QueueTable
                patients={state.patients}
                doctors={state.doctors}
                appointments={state.appointments}
                affectedPatients={q.preview?.affected_patients}
              />
            </div>
            <div>
              <DoctorStatus
                doctors={state.doctors}
                appointments={state.appointments}
                currentMinute={state.simulation?.current_minute ?? 0}
                utilization={state.metrics?.doctor_utilization ?? {}}
              />
            </div>
          </div>
          
          <ScheduleTimeline
            doctors={state.doctors}
            appointments={state.appointments}
            patients={state.patients}
            currentMinute={state.simulation?.current_minute ?? 0}
          />
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AlertsPanel alerts={state.alerts || []} />
            <AnalyticsCharts metrics={state.metrics} />
          </div>
          
          <DisruptionPanel
            text={q.disruptionText}
            onTextChange={q.setDisruptionText}
            onParse={q.parseDisruption}
            onPreview={q.previewDisruption}
            parsedActions={q.parsedActions}
            previewLoading={q.previewLoading}
          />
          
          {q.preview && (
            <ImpactComparison
              preview={q.preview}
              applyLoading={q.applyLoading}
              onApply={q.applyDisruption}
              onCancel={() => q.setParsedActions(null)}
            />
          )}
        </main>
      </div>
    </div>
  );
}
