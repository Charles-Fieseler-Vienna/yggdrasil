// Talking to `ygg serve`. Every call carries the per-run token embedded in the page.
const TOKEN = document.querySelector('meta[name="ygg-token"]').content;

async function call(method, path, body) {
  const opts = { method, headers: { "X-Ygg-Token": TOKEN } };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const r = await fetch("/api/" + path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join("; ") : data.detail;
    throw new Error(detail || "request failed (" + r.status + ")");
  }
  return data;
}

export const api = {
  graph: () => call("GET", "graph"),
  note: (id) => call("GET", "notes/" + encodeURIComponent(id)),
  createNote: (body) => call("POST", "notes", body),
  setFields: (id, body) => call("PATCH", "notes/" + encodeURIComponent(id), body),
  markDone: (id, body) => call("POST", "notes/" + encodeURIComponent(id) + "/done", body),
  link: (body) => call("POST", "relations", body),
  unlink: (id) => call("DELETE", "relations/" + encodeURIComponent(id)),
  overview: () => call("GET", "overview"),
  tick: (text) => call("POST", "todos/tick", { text }),
  answer: (id, text) => call("POST", "asks/answer", { id, text }),
  order: (ids) => call("POST", "agenda/order", { ids }),
};

// Calls onVersion(version) now and whenever the tree changes on disk; reconnects by itself.
export function watchVersion(onVersion) {
  const es = new EventSource("/api/events?t=" + encodeURIComponent(TOKEN));
  es.onmessage = (ev) => onVersion(JSON.parse(ev.data).version);
  return () => es.close();
}

// Per-vault browser storage for view state; best effort.
export const storage = {
  get(vault, key) {
    try { return JSON.parse(localStorage.getItem("ygg:" + vault + ":" + key)); } catch (e) { return null; }
  },
  set(vault, key, value) {
    try { localStorage.setItem("ygg:" + vault + ":" + key, JSON.stringify(value)); } catch (e) { /* optional */ }
  },
};
