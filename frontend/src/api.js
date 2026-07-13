const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function get(path) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}
async function post(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}

export const api = {
  customers: (limit = 20, band = "") =>
    get(`/customers?limit=${limit}${band ? `&band=${encodeURIComponent(band)}` : ""}`),
  customer: (id) => get(`/customers/${id}`),
  stats: () => get(`/stats`),
  score: (metrics) => post(`/score`, metrics),
  simulate: (metrics, changes) => post(`/simulate`, { metrics, changes }),
};
