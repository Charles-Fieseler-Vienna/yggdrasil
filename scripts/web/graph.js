// What is shown: pure functions over the graph from /api/graph, with no React or drawing.
//
// Layout edges run parent -> child: questions lead to follow-ups, claims and informing evidence,
// claims to their evidence, evidence to the sources and datasets it is derived from. A node is
// shown if it is a root of the view, or a child of a shown node that is unfolded.

export function layoutPair(e) {
  return e.rel === "derived-from" ? [e.source, e.target] : [e.target, e.source];
}

export function indexGraph(g) {
  g.byId = new Map(g.nodes.map((n) => [n.id, n]));
  g.byStem = new Map(g.nodes.map((n) => [n.stem, n]));
  return g;
}

// The nodes passing the filters, their layout parents and children, and the top roots.
// Notes superseded by another note, mapped to the newest note that replaces them.
export function supersededBy(G) {
  const newer = new Map();
  for (const e of G.edges) if (e.rel === "supersedes" && G.byId.has(e.source)) newer.set(e.target, e.source);
  const latest = new Map();
  for (const id of newer.keys()) {
    let x = id;
    const seen = new Set();
    while (newer.has(x) && !seen.has(x)) { seen.add(x); x = newer.get(x); }
    latest.set(id, x);
  }
  return latest;
}

// hiddenTypes may also hold "superseded": superseded notes are then left out, and the note replacing each
// takes its place, with its parents and children (so nothing under it is lost).
// With `only` (a test on notes, as for the frontier), the structure has only the notes passing it: a note
// whose parents all fail it becomes a root, and `cut` maps each note to the parents left out above it.
// Roots then come in order of rank (high priority, in progress, under an open issue) rather than by name.
export function structure(G, hiddenTypes, project, only) {
  const latest = hiddenTypes.has("superseded") ? supersededBy(G) : new Map();
  const now = (id) => latest.get(id) || id;
  const base = new Set(G.nodes.filter((n) => !hiddenTypes.has(n.type) && !latest.has(n.id) &&
    (!project || n.projects.includes(project) || !n.projects.length)).map((n) => n.id));  // and notes in no project
  const inSet = only ? new Set([...base].filter((id) => only(G.byId.get(id)))) : base;
  const parents = new Map(), children = new Map(), cut = new Map();
  for (const id of inSet) { parents.set(id, []); children.set(id, []); cut.set(id, []); }
  for (const e0 of G.edges) {
    if (latest.size && e0.rel === "supersedes") continue;
    const e = latest.size ? { ...e0, source: now(e0.source), target: now(e0.target) } : e0;
    if (e.source === e.target) continue;
    if (e.rel === "blocked-by" || !base.has(e.source) || !base.has(e.target)) continue;
    const [p, c] = layoutPair(e);
    if (!inSet.has(p) || !inSet.has(c)) {
      if (inSet.has(c) && !cut.get(c).includes(p)) cut.get(c).push(p);
      continue;
    }
    if (!children.get(p).includes(c)) children.get(p).push(c);
    if (!parents.get(c).includes(p)) parents.get(c).push(p);
  }
  const byStem = (a, b) => G.byId.get(a).stem.localeCompare(G.byId.get(b).stem);
  const rank = (id) => {
    const n = G.byId.get(id);
    return (n.meta.priority === "high" ? 0 : 4) + (n.status === "in-progress" ? 0 : 2) + (n.issues.length ? 0 : 1);
  };
  for (const list of children.values()) list.sort(byStem);
  const roots = [...inSet].filter((id) => !parents.get(id).length)
    .sort(only ? (a, b) => rank(a) - rank(b) || byStem(a, b) : byStem);
  return { inSet, parents, children, roots, cut };
}

export function defaultUnfolded(G, s) {
  return new Set(s.roots.filter((id) => G.byId.get(id).type === "question"));
}

export function descendants(s, id) {
  const seen = new Set();
  const stack = [id];
  while (stack.length) {
    const x = stack.pop();
    if (seen.has(x)) continue;
    seen.add(x);
    stack.push(...s.children.get(x));
  }
  return seen;
}

// A shortest path from a top root down to id, as a list of ids ending in id.
export function pathTo(s, id) {
  const next = new Map([[id, null]]);
  const queue = [id];
  while (queue.length) {
    const x = queue.shift();
    if (!s.parents.get(x).length) {
      const path = [];
      for (let y = x; y; y = next.get(y)) path.push(y);
      return path;
    }
    for (const p of s.parents.get(x)) if (!next.has(p)) { next.set(p, x); queue.push(p); }
  }
  return [id];
}

// A shortest path down from one node to a descendant, as a list of ids from `from` to `to`.
export function downPath(s, from, to) {
  const prev = new Map([[from, null]]);
  const queue = [from];
  while (queue.length) {
    const x = queue.shift();
    if (x === to) break;
    for (const c of s.children.get(x)) if (!prev.has(c)) { prev.set(c, x); queue.push(c); }
  }
  const path = [];
  for (let y = to; y; y = prev.get(y)) path.unshift(y);
  return path;
}

// Filters that show only some notes, each with the path up to its root for context; a `restrict` filter
// instead shows only its notes, cut loose from the rest (see structure).
export const FILTERS = {
  agenda: { label: "What the agent sees first", test: (n) => n.agenda.length > 0 },
  frontier: { label: "Frontier: the ways forward", restrict: true,
              test: (n) => ["open", "gap"].includes(n.flag) && !n.superseded && n.meta.priority !== "none" },
  "in-progress": { label: "In progress", test: (n) => n.status === "in-progress" },
  "not-done": { label: "Not done", test: (n) => n.status !== "done" },
  gap: { label: "Gaps", test: (n) => n.flag === "gap" },
  out: { label: "Out of scope", test: (n) => n.flag === "out" },
  issue: { label: "Under an open issue", test: (n) => n.issues.length > 0 },
  weak: { label: "Weak", test: (n) => ["low", "refuted"].includes(n.confidence) || ["failed", "ambiguous"].includes(n.outcome) },
  changed: { label: "Changed since…", test: (n, f) => !f.since || String(n.meta.dateModified || "").slice(0, 10) >= f.since },
  field: { label: "Field…", test: (n, f) => fieldMatches(n, f.key, f.value) },
};

// A frontmatter field matches if it holds the value (or any value, given none); case does not matter,
// and a list matches if any item does. "type" and "status" are fields too.
function fieldMatches(n, key, value) {
  if (!key) return true;
  const v = key === "type" ? n.type : n.meta[key];
  if (v === undefined || v === null || v === "") return false;
  const want = (value || "").trim().toLowerCase();
  return !want || [].concat(v).some((x) => String(x).toLowerCase().includes(want));
}

// The frontmatter fields notes use, for the field filter's menu.
export function fieldNames(G) {
  const keys = new Set(["type"]);
  for (const n of G.nodes) for (const k of Object.keys(n.meta)) keys.add(k);
  return [...keys].sort();
}

// The notes in the structure matching filter f ({kind, since, key, value}), or null for no filter.
export function filterMatches(G, s, f) {
  if (!f || !FILTERS[f.kind]) return null;
  return new Set([...s.inSet].filter((id) => FILTERS[f.kind].test(G.byId.get(id), f)));
}

// The view: shown nodes (with what folding each hides), the edges between them, and the tree to lay out.
// With a focus, the view is the focus and what is under it, with the focus as its only root.
// With a filter ({matches, unfolded}), it is the matches and every note above them, and folding
// is not used: a note's other children show only when it is in filter.unfolded.
export function computeView(G, s, unfolded, focus, filter) {
  const scope = focus ? descendants(s, focus) : s.inSet;
  const kids = (id) => s.children.get(id).filter((c) => scope.has(c));
  let keep = null;
  if (filter) {
    keep = new Set();
    const stack = [...filter.matches].filter((id) => scope.has(id));
    while (stack.length) {
      const id = stack.pop();
      if (keep.has(id)) continue;
      keep.add(id);
      stack.push(...s.parents.get(id).filter((p) => scope.has(p)));
    }
  }
  const isOpen = (id) => (filter ? filter.unfolded.has(id) : unfolded.has(id));
  const showKids = (id) => (filter ? kids(id).filter((c) => keep.has(c) || filter.unfolded.has(id))
                                   : unfolded.has(id) ? kids(id) : []);
  const roots = focus ? [focus] : filter ? s.roots.filter((r) => keep.has(r)) : s.roots;
  const shown = new Set();
  const stack = [...roots].reverse();
  while (stack.length) {
    const id = stack.pop();
    if (shown.has(id)) continue;
    shown.add(id);
    stack.push(...showKids(id).reverse());
  }
  const nodes = [...shown].map((id) => {
    const folded = !isOpen(id) && kids(id).some((c) => !shown.has(c));
    const from = s.cut && !s.parents.get(id).length ? s.cut.get(id).map((p) => G.byId.get(p)) : [];
    return { node: G.byId.get(id), folded, match: !filter || filter.matches.has(id), from,
             hidden: folded ? hiddenBelow(G, kids, shown, id) : { count: 0, gaps: 0 } };
  });
  const edges = [];
  for (const e of G.edges) {
    if (!shown.has(e.source) || !shown.has(e.target)) continue;
    if (e.rel === "blocked-by") { edges.push({ edge: e, from: e.source, to: e.target, cross: true, arrowAtEnd: true }); continue; }
    const [p, c] = layoutPair(e);
    edges.push({ edge: e, from: p, to: c, cross: false, arrowAtEnd: e.target === c });
  }
  // each shown node's shown children, in a fixed order (by filename), for the layout
  const shownKids = new Map([...shown].map((id) => [id, showKids(id).filter((c) => shown.has(c))]));
  return { nodes, edges, roots, kids: shownKids };
}

// What folding a shown node hides: its descendants not shown by another path.
function hiddenBelow(G, kids, shown, id) {
  const seen = new Set();
  const stack = kids(id).filter((c) => !shown.has(c));
  while (stack.length) {
    const c = stack.pop();
    if (seen.has(c)) continue;
    seen.add(c);
    stack.push(...kids(c).filter((x) => !shown.has(x)));
  }
  let gaps = 0;
  for (const c of seen) if (G.byId.get(c).flag === "gap") gaps++;
  return { count: seen.size, gaps };
}

// The relations allowed between notes of types a and b, either way round: {rel, dir}, where
// dir "out" means a REL b and "in" means b REL a. supersedes and blocked-by come last.
export function validRelations(schema, a, b) {
  const out = [];
  const add = (rel, dir) => { if (!out.some((x) => x.rel === rel && x.dir === dir)) out.push({ rel, dir }); };
  for (const [rel, r] of Object.entries(schema.relations)) {
    for (const [s, d] of r.pairs) {
      if (s === a && d === b) add(rel, "out");
      if (s === b && d === a) add(rel, "in");
    }
  }
  const rare = (x) => (x.rel === "supersedes" || x.rel === "blocked-by" ? 1 : 0);
  return out.sort((x, y) => rare(x) - rare(y));
}

export const BAD_TITLE = /[\\/:*?"<>|#^\[\]]/;

export function titleProblem(title) {
  if (!title.trim()) return "A title is needed.";
  if (BAD_TITLE.test(title)) return 'Titles cannot contain any of \\ / : * ? " < > | # ^ [ ]';
  return null;
}
