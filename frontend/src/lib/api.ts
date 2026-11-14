const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  getState: () => request<any>('/state'),
  getPatients: () => request<any[]>('/patients'),
  getDoctors: () => request<any[]>('/doctors'),
  getAnalytics: () => request<any>('/analytics'),
  optimize: () => request<any>('/optimize', { method: 'POST', body: '{}' }),
  parseDisruption: (text: string) =>
    request<any>('/disruptions/parse', { method: 'POST', body: JSON.stringify({ text }) }),
  previewDisruption: (actions: any[], state_version: number) =>
    request<any>('/disruptions/preview', {
      method: 'POST',
      body: JSON.stringify({ actions, expected_state_version: state_version }),
    }),
  applyDisruption: (preview_id: string, state_version: number) =>
    request<any>('/disruptions/apply', {
      method: 'POST',
      body: JSON.stringify({ preview_id, expected_state_version: state_version }),
    }),
  reset: () => request<any>('/reset', { method: 'POST', body: '{}' }),
  advanceSimulation: (minutes: number) =>
    request<any>('/simulation/advance', { method: 'POST', body: JSON.stringify({ minutes }) }),
  setSpeed: (speed: number) =>
    request<any>('/simulation/speed', { method: 'POST', body: JSON.stringify({ speed }) }),
  pauseSimulation: () =>
    request<any>('/simulation/pause', { method: 'POST', body: '{}' }),
  createPatient: (patient: any) =>
    request<any>('/patients', { method: 'POST', body: JSON.stringify(patient) }),
  getEvents: (limit: number = 30) =>
    request<any>(`/events?limit=${limit}`),
  setSimulationMode: (mode: string, enabled: boolean) =>
    request<any>('/simulation/mode', {
      method: 'POST',
      body: JSON.stringify({ mode, enabled }),
    }),
};
