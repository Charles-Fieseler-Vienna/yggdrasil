// Moving from one layout to the next smoothly. The new layout is shifted so that one node keeps
// its place (the node just folded or unfolded, else one already on screen), so the viewport never
// has to jump. Cards then glide to their new places; newly shown ones grow out of their nearest
// shown ancestor and fade in, and hidden ones shrink back into it and fade out.
import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { layoutView } from "./layout.js";

const DURATION = 320;
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

// The nearest node above id (through the layout parents) that `has` holds.
function ancestorIn(s, id, has) {
  const seen = new Set([id]);
  const queue = [...(s.parents.get(id) || [])];
  while (queue.length) {
    const p = queue.shift();
    if (seen.has(p)) continue;
    seen.add(p);
    if (has(p)) return p;
    queue.push(...(s.parents.get(p) || []));
  }
  return null;
}

// items: [{id, entry, x, y, w, h, opacity, leaving}] for the current frame, edges: the view's edges
// plus those of leaving nodes, and onPlaced(target positions) is called once per new layout.
export function useAnimatedLayout(view, s, keepId, onPlaced) {
  const shown = useRef(new Map());        // id -> {x, y, w, h, opacity, entry, to}, as last drawn
  const placed = useRef(null);            // the last layout, whose parent choices are kept
  const target = useMemo(() => view && layoutView(view, placed.current), [view]);
  const lastEdges = useRef([]);
  const raf = useRef(0);
  const [frame, setFrame] = useState({ items: [], edges: [] });

  useLayoutEffect(() => {
    if (!target) return;
    const old = shown.current;
    // shift the layout so a node that was already settled on screen stays where it is
    const settled = (id) => id && target[id] && old.has(id) && old.get(id).opacity === 1;
    const keep = [keepId, ...view.roots, ...Object.keys(target)].find(settled);
    const dx = keep ? old.get(keep).to.x - target[keep].x : 0;
    const dy = keep ? old.get(keep).to.y - target[keep].y : 0;
    const to = {};
    for (const [id, p] of Object.entries(target)) to[id] = { ...p, x: p.x + dx, y: p.y + dy };
    placed.current = to;
    onPlaced(to);

    const entries = new Map(view.nodes.map((v) => [v.node.id, v]));
    const moves = [];
    for (const [id, p] of Object.entries(to)) {
      const cur = old.get(id);
      if (cur) { moves.push({ id, entry: entries.get(id), from: cur, to: { ...p, opacity: 1 } }); continue; }
      const a = ancestorIn(s, id, (x) => old.has(x));
      const from = a ? { ...old.get(a), w: p.w, h: p.h, opacity: 0 } : { ...p, opacity: 0 };
      moves.push({ id, entry: entries.get(id), from, to: { ...p, opacity: 1 } });
    }
    for (const [id, cur] of old) {
      if (to[id] || cur.opacity === 0) continue;
      const a = ancestorIn(s, id, (x) => !!to[x]);
      moves.push({ id, entry: cur.entry, leaving: true, from: cur, to: { ...(a ? to[a] : cur), w: cur.w, h: cur.h, opacity: 0 } });
    }
    const leaving = new Set(moves.filter((m) => m.leaving).map((m) => m.id));
    const edges = view.edges.concat(lastEdges.current.filter((e) => leaving.has(e.from) || leaving.has(e.to)));
    lastEdges.current = view.edges;

    cancelAnimationFrame(raf.current);
    const start = performance.now();
    const step = (now) => {
      const t = ease(Math.min(1, (now - start) / DURATION));
      const done = t === 1;
      const next = new Map();
      const items = [];
      for (const m of moves) {
        const lerp = (k) => m.from[k] + (m.to[k] - m.from[k]) * t;
        const item = { id: m.id, entry: m.entry, leaving: !!m.leaving, x: lerp("x"), y: lerp("y"),
                       w: m.to.w, h: m.to.h, opacity: done ? m.to.opacity : lerp("opacity") };
        if (!(done && m.leaving)) items.push(item);
        next.set(m.id, { ...item, to: m.to });
      }
      shown.current = next;
      setFrame({ items, edges: done ? view.edges : edges });
      if (!done) raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf.current);
  }, [target]);

  return frame;
}
