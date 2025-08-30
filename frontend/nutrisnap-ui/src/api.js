const BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "") || "";

export async function analyzeImage(file) {
  const fd = new FormData();
  fd.append("image", file);
  const r = await fetch(`${BASE}/analyze`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(`Analyze failed: ${r.status}`);
  return r.json();
}

export async function fetchHistory(limit = 20) {
  const url = new URL(`${BASE}/history`);
  url.searchParams.set("limit", String(limit));
  const r = await fetch(url.toString());
  if (!r.ok) throw new Error(`History failed: ${r.status}`);
  return r.json();
}

export async function fetchNutrition(food) {
  const url = new URL(`${BASE}/nutrition`);
  url.searchParams.set("food", food);
  const r = await fetch(url.toString());
  if (!r.ok) throw new Error(`Nutrition failed: ${r.status}`);
  return r.json();
}
