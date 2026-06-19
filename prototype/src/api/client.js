/**
 * API client for the MBSSE FastAPI backend.
 * Handles base URL, Bearer token injection, and token refresh.
 *
 * DEMO MODE: when VITE_API_URL is not set (e.g. static deploy without a
 * backend), auth falls back to hardcoded demo credentials and data calls
 * return an empty/mock response rather than throwing "Failed to fetch".
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';

// ── Demo mode ────────────────────────────────────────────────────────────────
// Active when no API URL is configured (static-only deploy).
export const DEMO_MODE = !import.meta.env.VITE_API_URL;

/** True when we should use local mock data — covers both no-backend deploys
 *  and sessions that logged in with demo credentials (token = 'demo-token'). */
export const usesDemoData = () =>
  DEMO_MODE || localStorage.getItem('access_token') === 'demo-token';

const DEMO_USERS = [
  { email: 'admin@mbsse.gov.sl',  password: 'demo2026', role: 'admin',   name: 'MBSSE Administrator' },
  { email: 'partner@example.com', password: 'demo2026', role: 'partner', name: 'Partner User' },
  { email: 'viewer@example.com',  password: 'demo2026', role: 'viewer',  name: 'Viewer User' },
];

// ── Token storage ────────────────────────────────────────────────────────────
// Stored in localStorage so they survive page refresh.
// For higher security in production consider httpOnly cookies instead.

export const auth = {
  getAccessToken: () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  setTokens: ({ access_token, refresh_token }) => {
    localStorage.setItem('access_token', access_token);
    if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
  },
  setUser: (user) => localStorage.setItem('mbsse_user', JSON.stringify(user)),
  getUser: () => {
    try { return JSON.parse(localStorage.getItem('mbsse_user')); } catch { return null; }
  },
  clear: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('mbsse_user');
  },
  isLoggedIn: () => !!localStorage.getItem('access_token'),
};

// ── Core fetch wrapper ───────────────────────────────────────────────────────

let isRefreshing = false;
let refreshQueue = []; // callbacks waiting for the new token

async function refreshAccessToken() {
  const refreshToken = auth.getRefreshToken();
  if (!refreshToken) throw new Error('No refresh token');

  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    auth.clear();
    throw new Error('Session expired — please log in again');
  }

  const data = await res.json();
  auth.setTokens({ access_token: data.access_token });
  return data.access_token;
}

/**
 * Makes an authenticated request. Automatically refreshes the access token
 * on 401 and retries once.
 */
export async function apiFetch(path, options = {}) {
  const token = auth.getAccessToken();
  const headers = {
    // Don't set Content-Type for FormData — the browser must set it with the multipart boundary
    ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  let res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  // Token expired — try to refresh once
  if (res.status === 401 && auth.getRefreshToken()) {
    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const newToken = await refreshAccessToken();
        refreshQueue.forEach((cb) => cb(newToken));
        refreshQueue = [];
      } catch (err) {
        refreshQueue.forEach((cb) => cb(null));
        refreshQueue = [];
        isRefreshing = false;
        throw err;
      }
      isRefreshing = false;
    } else {
      // Another request is already refreshing — queue this one
      await new Promise((resolve) => refreshQueue.push(resolve));
    }

    // Retry with new token
    const newToken = auth.getAccessToken();
    res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: { ...headers, Authorization: `Bearer ${newToken}` },
    });
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    const msg = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map(e => e.msg ?? JSON.stringify(e)).join('; ')
        : `HTTP ${res.status}`;
    throw new Error(msg);
  }

  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

// ── Auth API calls ────────────────────────────────────────────────────────────

export const authApi = {
  login: async (email, password) => {
    try {
      return await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
    } catch (err) {
      // Network error (backend unreachable) → try demo credentials
      if (err.message === 'Failed to fetch' || err.message.includes('NetworkError')) {
        const demo = DEMO_USERS.find(
          u => u.email === email && u.password === password
        );
        if (demo) {
          return {
            access_token:  'demo-token',
            refresh_token: 'demo-refresh',
            role:          demo.role,
            full_name:     demo.name,
            org_id:        null,
          };
        }
        throw new Error('Could not reach the server. Use demo credentials to explore the prototype.');
      }
      throw err;
    }
  },

  logout: () =>
    apiFetch('/auth/logout', { method: 'POST' }).catch(() => {}).finally(() => auth.clear()),
};

// ── Organisations API calls ──────────────────────────────────────────────

export const organisationsApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    // Trailing slash avoids a cross-origin 307 redirect (FastAPI route is "/")
    return apiFetch(`/organisations/${qs ? '?' + qs : ''}`)
      .catch(err => {
        if (err.message === 'Failed to fetch' || err.message.includes('NetworkError')) return [];
        throw err;
      });
  },
  get: (id) => apiFetch(`/organisations/${id}`),
  /** Admin only: create a new partner organisation. */
  create: (data) => apiFetch('/organisations/', { method: 'POST', body: JSON.stringify(data) }),
  /** Admin (all fields) or partner (contact fields only) update. */
  patch: (id, data) => apiFetch(`/organisations/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
};

// ── Users API calls (admin) ───────────────────────────────────────────────────

export const usersApi = {
  list:         ()         => apiFetch('/users'),
  create:       (data)     => apiFetch('/users',                  { method: 'POST',   body: JSON.stringify(data) }),
  update:       (id, data) => apiFetch(`/users/${id}`,            { method: 'PATCH',  body: JSON.stringify(data) }),
  deactivate:   (id)       => apiFetch(`/users/${id}/deactivate`, { method: 'POST' }),
  reactivate:   (id)       => apiFetch(`/users/${id}/reactivate`, { method: 'POST' }),
  resendInvite: (id)       => apiFetch(`/users/${id}/resend-invite`, { method: 'POST' }),
  remove:       (id)       => apiFetch(`/users/${id}`,            { method: 'DELETE' }),
};

// ── Reminders API calls (admin) ───────────────────────────────────────────────

export const remindersApi = {
  /** Trigger an immediate bulk reminder send. Returns { sent, message }. */
  sendBulk: () => apiFetch('/reminders/send-bulk', { method: 'POST' }),
  /** List the reminder log. */
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/reminders/${qs ? '?' + qs : ''}`);
  },
};

// ── Submissions API calls ────────────────────────────────────────────────────

export const submissionsApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    // Trailing slash avoids a cross-origin 307 redirect (FastAPI route is "/")
    return apiFetch(`/submissions/${qs ? '?' + qs : ''}`);
  },
  get: (id) => apiFetch(`/submissions/${id}`),
  /** Consolidated submission-level report submit (resolves period/project server-side). */
  submitReport: (data) => apiFetch('/submissions/submit-report', { method: 'POST', body: JSON.stringify(data) }),
  create: (data) => apiFetch('/submissions/', { method: 'POST', body: JSON.stringify(data) }),
  saveDraft: (id, data) => apiFetch(`/submissions/${id}/draft`, { method: 'PATCH', body: JSON.stringify(data) }),
  submit: (id, data) => apiFetch(`/submissions/${id}/submit`, { method: 'POST', body: JSON.stringify(data) }),
  adminPatch: (id, data) => apiFetch(`/submissions/${id}/admin`, { method: 'PATCH', body: JSON.stringify(data) }),
  uploadFile: (id, file, fileKind) => {
    const form = new FormData();
    // FastAPI parameter name is 'upload' (must match the route declaration)
    form.append('upload', file);
    return apiFetch(`/submissions/${id}/files?file_kind=${fileKind}`, {
      method: 'POST',
      body: form,
    });
  },
};
