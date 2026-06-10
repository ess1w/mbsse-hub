/**
 * API client methods for GEM Coordinator monthly reports.
 * Mirrors the pattern used by submissionsApi in client.js.
 */
import { apiFetch, usesDemoData } from './client.js';

// Demo-mode mock data
const DEMO_REPORTS = [];

export const gemReportsApi = {
  list: () => {
    if (usesDemoData()) return Promise.resolve(DEMO_REPORTS);
    return apiFetch('/gem-reports/');
  },
  get: (id) => {
    if (usesDemoData()) return Promise.resolve(DEMO_REPORTS.find(r => r.id === id) ?? null);
    return apiFetch(`/gem-reports/${id}`);
  },
  create: (data) => {
    if (usesDemoData()) {
      const rec = { ...data, id: crypto.randomUUID(), status: 'draft', created_at: new Date().toISOString() };
      DEMO_REPORTS.push(rec);
      return Promise.resolve(rec);
    }
    return apiFetch('/gem-reports', { method: 'POST', body: JSON.stringify(data) });
  },
  update: (id, data) => {
    if (usesDemoData()) {
      const idx = DEMO_REPORTS.findIndex(r => r.id === id);
      if (idx !== -1) DEMO_REPORTS[idx] = { ...DEMO_REPORTS[idx], ...data };
      return Promise.resolve(DEMO_REPORTS[idx]);
    }
    return apiFetch(`/gem-reports/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  },
  submit: (id) => {
    if (usesDemoData()) {
      const idx = DEMO_REPORTS.findIndex(r => r.id === id);
      if (idx !== -1) DEMO_REPORTS[idx].status = 'submitted';
      return Promise.resolve(DEMO_REPORTS[idx]);
    }
    return apiFetch(`/gem-reports/${id}/submit`, { method: 'POST' });
  },
};
