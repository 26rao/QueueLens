import { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import type { Patient, Doctor, Appointment } from '../../types';
import { minuteToTime, priorityColor, statusColor } from '../../lib/utils';

interface QueueTableProps {
  patients: Patient[];
  doctors: Doctor[];
  appointments: Appointment[];
  affectedPatients?: string[];
}

export function QueueTable({ patients, doctors, appointments, affectedPatients = [] }: QueueTableProps) {
  const [sortField, setSortField] = useState<string>('priority');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [filter, setFilter] = useState('');

  const doctorMap = Object.fromEntries(doctors.map(d => [d.id, d]));
  const apptMap = Object.fromEntries(appointments.map(a => [a.patient_id, a]));

  const priorityOrder: Record<string, number> = { emergency: 0, urgent: 1, normal: 2 };

  const sorted = [...patients]
    .filter(p => !filter || p.name.toLowerCase().includes(filter.toLowerCase()) ||
      p.priority.includes(filter.toLowerCase()) || p.status.includes(filter.toLowerCase()))
    .sort((a, b) => {
      let va: any = a[sortField as keyof Patient];
      let vb: any = b[sortField as keyof Patient];
      if (sortField === 'priority') { va = priorityOrder[a.priority]; vb = priorityOrder[b.priority]; }
      if (sortDir === 'asc') return va > vb ? 1 : -1;
      return va < vb ? 1 : -1;
    });

  const toggleSort = (field: string) => {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortDir('asc'); }
  };

  const SortIcon = ({ field }: { field: string }) => sortField === field
    ? (sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)
    : null;

  return (
    <div id="queue" className="bg-white rounded-xl border border-gray-100 shadow-sm">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <h2 className="font-semibold text-slate-900">Live Patient Queue</h2>
        <input
          type="text"
          placeholder="Filter patients..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 w-48 focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-gray-500 text-xs uppercase">
              {[
                ['name', 'Patient'], ['priority', 'Priority'],
                ['required_specialty', 'Specialty'], ['doctor', 'Doctor'],
                ['start', 'Est. Start'], ['wait', 'Wait'], ['status', 'Status']
              ].map(([field, label]) => (
                <th key={field}
                  onClick={() => toggleSort(field)}
                  className="text-left px-4 py-3 cursor-pointer hover:text-slate-700 select-none"
                >
                  <div className="flex items-center gap-1">
                    {label}
                    <SortIcon field={field} />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 && (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">No patients found</td></tr>
            )}
            {sorted.map(p => {
              const appt = apptMap[p.id];
              const doctor = appt ? doctorMap[appt.doctor_id] : null;
              const wait = appt ? Math.max(0, appt.start_minute - p.arrival_minute) : null;
              const isAffected = affectedPatients.includes(p.id);
              return (
                <tr key={p.id}
                  className={`border-t border-gray-50 hover:bg-gray-50 transition-colors ${isAffected ? 'bg-amber-50' : ''}`}>
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {p.name}
                    {isAffected && <span className="ml-2 text-xs text-amber-600">●</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${priorityColor(p.priority)}`}>
                      {p.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{p.required_specialty}</td>
                  <td className="px-4 py-3 text-gray-600">{doctor?.name || '—'}</td>
                  <td className="px-4 py-3 font-mono text-gray-700">
                    {appt ? minuteToTime(appt.start_minute) : '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {wait !== null ? `${wait} min` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(p.status)}`}>
                      {p.status.replace('_', ' ')}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
