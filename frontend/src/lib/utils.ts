import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function minuteToTime(minute: number): string {
  const totalMinutes = 8 * 60 + minute; // base 08:00
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
}

export function priorityColor(priority: string): string {
  switch (priority) {
    case 'emergency': return 'text-red-600 bg-red-50';
    case 'urgent': return 'text-amber-600 bg-amber-50';
    default: return 'text-teal-600 bg-teal-50';
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case 'in_progress': return 'text-blue-600 bg-blue-50';
    case 'completed': return 'text-gray-500 bg-gray-50';
    case 'waiting': return 'text-amber-600 bg-amber-50';
    case 'scheduled': return 'text-teal-600 bg-teal-50';
    case 'unscheduled': return 'text-red-600 bg-red-50';
    default: return 'text-gray-600 bg-gray-50';
  }
}
