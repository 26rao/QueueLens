import type { Doctor, Appointment, Patient } from '../../types';
import { minuteToTime } from '../../lib/utils';

interface ScheduleTimelineProps {
  doctors: Doctor[];
  appointments: Appointment[];
  patients: Patient[];
  currentMinute: number;
  horizon?: number;
}

const PRIORITY_COLORS: Record<string, string> = {
  emergency: '#DC2626',
  urgent: '#D97706',
  normal: '#0D9488',
};

export function ScheduleTimeline({ doctors, appointments, patients, currentMinute, horizon = 480 }: ScheduleTimelineProps) {
  const patientMap = Object.fromEntries(patients.map(p => [p.id, p]));
  const scale = (min: number) => `${Math.max(0, Math.min(100, (min / horizon) * 100))}%`;

  return (
    <div id="timeline" className="bg-white rounded-xl border border-gray-100 shadow-sm">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <h2 className="font-semibold text-slate-900">Scheduling Timeline</h2>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-600 inline-block"/>Emergency</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-600 inline-block"/>Urgent</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-teal-600 inline-block"/>Normal</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-gray-400 inline-block"/>Unavailable</span>
        </div>
      </div>
      <div className="p-4 overflow-x-auto">
        <div className="min-w-[680px]">
          {/* Time axis */}
          <div className="flex mb-2 ml-24">
            {[0, 60, 120, 180, 240, 300, 360, 420, 480].map(m => (
              <div key={m} className="flex-1 text-xs text-gray-400 font-mono">{minuteToTime(m)}</div>
            ))}
          </div>
          {doctors.map(doc => {
            const docAppts = appointments.filter(a => a.doctor_id === doc.id && a.status !== 'cancelled');
            return (
              <div key={doc.id} className="flex items-center mb-2 h-10">
                <div className="w-24 text-xs text-gray-600 font-medium pr-2 truncate">{doc.name}</div>
                <div className="flex-1 relative h-8 bg-gray-50 rounded">
                  {/* Unavailability blocks */}
                  {doc.unavailabilities?.map((u, i) => (
                    <div
                      key={i}
                      className="absolute h-full bg-gray-300 opacity-70 rounded"
                      style={{
                        left: scale(u.start_minute),
                        width: `${Math.max(0, Math.min(100, ((u.end_minute - u.start_minute) / horizon) * 100))}%`
                      }}
                      title={u.reason}
                    />
                  ))}
                  {/* Appointment blocks */}
                  {docAppts.map(appt => {
                    const patient = patientMap[appt.patient_id];
                    const color = PRIORITY_COLORS[patient?.priority ?? 'normal'] || '#0D9488';
                    return (
                      <div
                        key={appt.id}
                        className="absolute h-full rounded text-white text-xs flex items-center px-1 overflow-hidden"
                        style={{
                          left: scale(appt.start_minute),
                          width: `${Math.max(0, Math.min(100, ((appt.end_minute - appt.start_minute) / horizon) * 100))}%`,
                          backgroundColor: color,
                          opacity: appt.status === 'completed' ? 0.5 : 1,
                        }}
                        title={`${patient?.name || appt.patient_id} (${patient?.priority || 'normal'}) ${minuteToTime(appt.start_minute)}–${minuteToTime(appt.end_minute)}`}
                      >
                        <span className="truncate">{patient?.name?.split(' ')[1] ?? appt.patient_id}</span>
                      </div>
                    );
                  })}
                  {/* Current time indicator */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-blue-500 z-10"
                    style={{ left: scale(currentMinute) }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
