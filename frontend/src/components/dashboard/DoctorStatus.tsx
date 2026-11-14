import type { Doctor, Appointment } from '../../types';

interface DoctorStatusProps {
  doctors: Doctor[];
  appointments: Appointment[];
  currentMinute: number;
  utilization: Record<string, number>;
}

function getDoctorStatus(doctor: Doctor, appointments: Appointment[], currentMinute: number): string {
  if (!doctor.active) return 'off-shift';
  const unav = doctor.unavailabilities?.find(
    u => u.start_minute <= currentMinute && u.end_minute > currentMinute
  );
  if (unav) return 'unavailable';
  const busy = appointments.find(
    a => a.doctor_id === doctor.id && a.status === 'in_progress'
  );
  if (busy) return 'busy';
  return 'available';
}

const statusStyles: Record<string, string> = {
  available: 'text-teal-600 bg-teal-50',
  busy: 'text-blue-600 bg-blue-50',
  unavailable: 'text-red-600 bg-red-50',
  'off-shift': 'text-gray-500 bg-gray-50',
};

export function DoctorStatus({ doctors, appointments, currentMinute, utilization }: DoctorStatusProps) {
  return (
    <div id="doctors" className="bg-white rounded-xl border border-gray-100 shadow-sm">
      <div className="p-4 border-b border-gray-100">
        <h2 className="font-semibold text-slate-900">Doctor Availability</h2>
      </div>
      <div className="p-4 space-y-3">
        {doctors.map(d => {
          const status = getDoctorStatus(d, appointments, currentMinute);
          const util = utilization[d.id] ?? 0;
          const docAppts = appointments.filter(a => a.doctor_id === d.id && a.status !== 'cancelled');
          return (
            <div key={d.id} className="p-3 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="font-medium text-slate-800 text-sm">{d.name}</span>
                  <div className="text-xs text-gray-500">{d.specialties?.join(', ')}</div>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusStyles[status] || statusStyles.available}`}>
                  {status}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>{docAppts.length} appts</span>
                <span>Util: {util}%</span>
              </div>
              <div className="mt-2 w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className="bg-teal-500 h-1.5 rounded-full transition-all"
                  style={{ width: `${Math.min(util, 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
