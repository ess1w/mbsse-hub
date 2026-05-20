/**
 * API client for the MBSSE FastAPI backend.
 * Handles base URL, Bearer token injection, and token refresh.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';

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
    'Content-Type': 'application/json',
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
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }

  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

// ── Auth API calls ────────────────────────────────────────────────────────────

export const authApi = {
  login: (email, password) =>
    apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  logout: () =>
    apiFetch('/auth/logout', { method: 'POST' }).finally(() => auth.clear()),
};

// ── Organisations API calls ──────────────────────────────────────────────

export const organisationsApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/organisations${qs ? '?' + qs : ''}`);
  },
  get: (id) => apiFetch(`/organisations/${id}`),
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

// ── Submissions API calls ────────────────────────────────────────────────────

export const submissionsApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/submissions${qs ? '?' + qs : ''}`);
  },
  get: (id) => apiFetch(`/submissions/${id}`),
  create: (data) => apiFetch('/submissions', { method: 'POST', body: JSON.stringify(data) }),
  saveDraft: (id, data) => apiFetch(`/submissions/${id}/draft`, { method: 'PATCH', body: JSON.stringify(data) }),
  submit: (id, data) => apiFetch(`/submissions/${id}/submit`, { method: 'POST', body: JSON.stringify(data) }),
  adminPatch: (id, data) => apiFetch(`/submissions/${id}/admin`, { method: 'PATCH', body: JSON.stringify(data) }),
  uploadFile: (id, file, fileKind) => {
    const form = new FormData();
    form.append('file', file);
    // Remove Content-Type so the browser sets the multipart boundary automatically
    return apiFetch(`/submissions/${id}/files?file_kind=${fileKind}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${auth.getAccessToken()}` },
      body: form,
    });
  },
};
