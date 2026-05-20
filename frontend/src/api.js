const BASE = import.meta.env.VITE_API_URL || '/api';

async function req(path, opts = {}) {
  const url = `${BASE}${path}`;
  const method = opts.method || 'GET';
  console.log(`[API] ${method} ${url}`);
  
  try {
    const res = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': opts.body ? 'application/json' : undefined,
      },
      ...opts,
    });

    const text = await res.text();
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('text/html') || text.trim().startsWith('<')) {
      console.error(`[API] Received HTML instead of JSON from ${url}`);
      console.error(text.slice(0, 500));
      throw new Error('Server error: Received HTML response from API. Check that the backend endpoint is correct and the Django server is returning JSON.');
    }

    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      console.error(`[API] Failed to parse JSON from ${url}`, res.status);
      console.error(text.slice(0, 500));
      throw new Error(`Server error: Invalid response format. Status ${res.status}`);
    }

    if (!res.ok) {
      const errorMsg = data?.error || `Request failed with status ${res.status}`;
      console.error(`[API] Error ${res.status}: ${errorMsg}`);
      throw new Error(errorMsg);
    }

    return data;
  } catch (err) {
    if (err instanceof TypeError) {
      const msg = 'Connection error: Unable to reach the server. Please check if the barangay server is running. (Backend should be on http://localhost:8000)';
      console.error('[API] Connection failed:', msg);
      throw new Error(msg);
    }
    console.error('[API] Request failed:', err.message);
    throw err;
  }
}

export const api = {
  getStatus:         (id)    => req(`/status/${id}/`),
  getRequest:        (id)    => req(`/requests/${id}/`),
  listRequests:      (params) => req(`/requests/?${new URLSearchParams(params)}`),
  getSummary:        ()      => req('/summary/'),
  getAppointment:    (id)    => req(`/appointments/${id}/`),
  createAppointment: (body)  => req('/appointments/', { method:'POST', body: JSON.stringify(body) }),
  getTimeslots:      ()      => req('/timeslots/'),
  healthCheck:       ()      => req('/health/'),
};

// Log API URL for debugging
console.log(`[API] Using backend URL: ${BASE}`);
