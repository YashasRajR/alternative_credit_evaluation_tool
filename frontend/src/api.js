async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, options);
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

export const api = {
  health: () => request("/health"),
  crops: () => request("/crops"),
  stats: () => request("/stats"),
  list: (q = "") => request(`/assessments?q=${encodeURIComponent(q)}`),
  get: (id) => request(`/assessments/${id}`),
  remove: (id) => request(`/assessments/${id}`, { method: "DELETE" }),
  create: (body) =>
    request("/assessments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};

export const rupees = (n) =>
  n === null || n === undefined ? "–" : "₹" + Math.round(n).toLocaleString("en-IN");

export const pct = (n, digits = 0) => (n === null || n === undefined ? "–" : `${(n * 100).toFixed(digits)}%`);
