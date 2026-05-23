const BASE = import.meta.env.VITE_API_URL || 'https://zapatrack-api.onrender.com/api';

async function req(path, opts = {}) {
  const url = `${BASE}${path}`;
  const method = opts.method || 'GET';
  console.log(`[API] ${method} ${url}`);

  const headers = {
    Accept: 'application/json',
    ...(opts.body ? { 'Content-Type': 'application/json' } : {}),
  };

  try {
    const res = await fetch(url, { ...opts, headers });

    const text = await res.text();
    const contentType = res.headers.get('content-type') || '';

    if (contentType.includes('text/html') || text.trim().startsWith('<')) {
      console.error(`[API] HTML response from ${url}:`, text.slice(0, 300));
      throw new Error('Server returned HTML instead of JSON. Check your backend URL.');
    }

    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      throw new Error(`Invalid JSON from server. Status ${res.status}`);
    }

    if (!res.ok) {
      throw new Error(data?.error || data?.detail || `Request failed: ${res.status}`);
    }

    return data;
  } catch (err) {
    if (err instanceof TypeError) {
      throw new Error(`Cannot reach server at ${BASE}. Is the backend running?`);
    }
    throw err;
  }
}

export const api = {
  getStatus:         (id)     => req(`/status/${id}/`),
  getRequest:        (id)     => req(`/requests/${id}/`),
  listRequests:      (params) => req(`/requests/?${new URLSearchParams(params)}`),
  getSummary:        ()       => req('/summary/'),
  getAppointment:    (id)     => req(`/appointments/${id}/`),
  createAppointment: (body)   => req('/appointments/', { method: 'POST', body: JSON.stringify(body) }),
  getTimeslots:      ()       => req('/timeslots/'),
  healthCheck:       ()       => req('/health/'),
};

console.log(`[API] Using backend: ${BASE}`);