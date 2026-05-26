const BASE = "/api";

function getToken() {
  return localStorage.getItem("access_token");
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401 && token) {
    // Try refresh
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      const refreshRes = await fetch(`${BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (refreshRes.ok) {
        const data = await refreshRes.json();
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        return request(path, options);
      }
    }
    localStorage.clear();
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || "Request failed");
  }
  return data;
}

export const api = {
  // Auth
  register: (email, password) =>
    request("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request("/auth/me"),

  // API Keys
  listKeys: () => request("/keys"),
  createKey: (name) => request("/keys", { method: "POST", body: JSON.stringify({ name }) }),
  deleteKey: (id) => request(`/keys/${id}`, { method: "DELETE" }),

  // Provider Keys
  listProviderKeys: () => request("/providers/keys"),
  addProviderKey: (provider, apiKey) =>
    request("/providers/keys", { method: "POST", body: JSON.stringify({ provider, api_key: apiKey }) }),
  deleteProviderKey: (id) => request(`/providers/keys/${id}`, { method: "DELETE" }),

  // Billing
  billingStatus: () => request("/billing/status"),
  createCheckout: (successUrl, cancelUrl) =>
    request("/billing/checkout", {
      method: "POST",
      body: JSON.stringify({ success_url: successUrl, cancel_url: cancelUrl }),
    }),
  createPortal: (returnUrl) =>
    request(`/billing/portal?return_url=${encodeURIComponent(returnUrl)}`, { method: "POST" }),

  // Analytics
  analyticsOverview: () => request("/analytics/overview"),
  analyticsUsage: (days = 30) => request(`/analytics/usage?days=${days}`),
  analyticsProviders: () => request("/analytics/providers"),
  analyticsHealth: () => request("/analytics/health"),

  // Proxy
  listModels: () => request("/v1/models"),

  // Health
  health: () => request("/health"),
};
