// The ygg web app: the tree as a foldable graph, with a side panel and dialogs for editing it.
//
// State is the graph from the server plus the view: which nodes are unfolded, the filters (type,
// project, and a note filter such as "in progress"), and an optional focus (a note shown as the only root, reached along a trail of notes). Everything drawn is derived from those.
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Background, Controls, MiniMap, ReactFlow, ReactFlowProvider, useReactFlow } from "@xyflow/react";
import { api, storage, watchVersion } from "./api.js";
import { FILTERS, computeView, defaultUnfolded, descendants, downPath, filterMatches, indexGraph, pathTo, structure, supersededBy } from "./graph.js";
import { bounds } from "./layout.js";
import { useAnimatedLayout } from "./animate.js";
import { html } from "./html.js";
import { nodeTypes } from "./note.js";
import { edgeTypes } from "./edges.js";
import { Breadcrumb, Toolbar } from "./toolbar.js";
import { Panel } from "./panel.js";
import { DIALOGS } from "./dialogs.js";

const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

// Where a card's edges attach: mid-left in and mid-right out between columns; top and bottom, or the right
// side, between cards in one column. Given to React Flow rather than measured (see the nodes below).
function handles(w, h) {
  const at = { left: [0, h / 2 - 0.5], right: [w - 1, h / 2 - 0.5], top: [w / 2 - 0.5, 0], bottom: [w / 2 - 0.5, h - 1] };
  return [["target", "left"], ["target", "top"], ["target", "bottom"], ["target", "right"],
          ["source", "right"], ["source", "top"], ["source", "bottom"]]
    .map(([type, side]) => ({ id: side, type, position: side, x: at[side][0], y: at[side][1], width: 1, height: 1 }));
}

// The sides an edge leaves and enters by: right to left between columns. Within a column, bottom to top
// when the two cards are next to each other, and out and back in on the right when other cards sit between.
function sides(at, from, to) {
  const a = at.get(from), b = at.get(to);
  if (Math.abs(a.x - b.x) >= Math.min(a.w, b.w) / 2) return ["right", "left"];
  const [top, bottom] = a.y < b.y ? [a, b] : [b, a];
  const between = [...at.values()].some((c) => c !== a && c !== b && Math.abs(c.x - a.x) < a.w / 2 &&
                                           c.y > top.y && c.y < bottom.y);
  if (between) return ["right", "right"];
  return a.y < b.y ? ["bottom", "top"] : ["top", "bottom"];
}

function App() {
  const flow = useReactFlow();
  const [G, setG] = useState(null);
  window.__G = G;  // for tests and the console
  const [unfolded, setUnfolded] = useState(null);   // null: the default for the current filters
  const [hiddenTypes, setHiddenTypes] = useState(new Set(["superseded"]));
  const [project, setProject] = useState("");
  const [filter, setFilterState] = useState(null);   // {kind, since, key, value}, see FILTERS
  const [filterUnfolded, setFilterUnfolded] = useState(new Set());  // notes whose other children a filter shows
  const [trail, setTrail] = useState([]);            // the focus path, top root first; the focus is last
  const [selected, setSelected] = useState(null);
  const [connectFrom, setConnectFrom] = useState(null);
  const [dialog, setDialog] = useState(null);         // {kind, ...props}
  const [toast, setToast] = useState(null);           // {text, error}
  const [offsets, setOffsets] = useState({});         // id -> {dx, dy}: where the user dragged a card, from its place in the layout
  const after = useRef({ fit: true });                // what the next layout should do: {anchor | fit | center}

  // --- Loading ---

  const load = useCallback(async () => {
    const g = indexGraph(await api.graph());
    setG((prev) => {
      if (!prev) {
        const saved = storage.get(g.vault, "view") || {};
        if (saved.unfolded) setUnfolded(new Set(saved.unfolded));
        // views saved before superseded notes could be hidden (no v) start with them hidden too
        setHiddenTypes(new Set(saved.v ? saved.hiddenTypes : (saved.hiddenTypes || []).concat(["superseded"])));
        setProject(saved.project || "");
        setTrail(saved.trail || []);
        setFilterState(saved.filter || null);
        setOffsets(storage.get(g.vault, "offsets") || {});
      }
      return g;
    });
    if (g.errors.length) setToast({ text: "Some notes could not be read:\n" + g.errors.join("\n"), error: true });
    return g;
  }, []);

  const version = useRef(null);
  useEffect(() => {
    load().catch((e) => setToast({ text: e.message, error: true }));
    return watchVersion((v) => {
      if (version.current !== null && v !== version.current) load().catch(() => {});
      version.current = v;
    });
  }, [load]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), toast.error ? 8000 : 3500);
    return () => clearTimeout(t);
  }, [toast]);

  // --- The view ---

  const spec = filter && FILTERS[filter.kind];
  const restrict = spec && spec.restrict ? (n) => spec.test(n, filter) : null;  // the frontier: only its notes
  const s = useMemo(() => G && structure(G, hiddenTypes, project, restrict), [G, hiddenTypes, project, restrict && filter.kind]);
  const unf = useMemo(() => unfolded || (s ? defaultUnfolded(G, s) : new Set()), [unfolded, s]);
  const foc = trail.length && s && trail.every((id) => s.inSet.has(id)) ? trail[trail.length - 1] : null;
  const matches = useMemo(() => s && filterMatches(G, s, filter), [s, filter]);
  const view = useMemo(() => s && computeView(G, s, unf, foc, matches && { matches, unfolded: filterUnfolded }),
                       [s, unf, foc, matches, filterUnfolded]);
  useEffect(() => {
    if (G) storage.set(G.vault, "view", { v: 2, unfolded: unfolded && [...unfolded], hiddenTypes: [...hiddenTypes], project, trail, filter });
  }, [G && G.vault, unfolded, hiddenTypes, project, trail, filter]);

  // Once a new layout is placed: fit the viewport to it, or centre a note, as the change asked.
  const onPlaced = (placed) => {
    const to = {};
    for (const [id, p] of Object.entries(placed)) to[id] = offsets[id] ? { ...p, x: p.x + offsets[id].dx, y: p.y + offsets[id].dy } : p;
    const todo = after.current;
    after.current = {};
    if (todo.center && to[todo.center]) {
      const p = to[todo.center];
      flow.setCenter(p.x + p.w / 2, p.y + p.h / 2, { zoom: Math.max(flow.getZoom(), 0.85), duration: 320 });
    } else if (todo.fit && Object.keys(to).length) {
      flow.fitBounds(bounds(to), { padding: 0.12, duration: 320 });
    }
  };
  const frame = useAnimatedLayout(view, s, after.current.anchor, onPlaced);

  const nodes = useMemo(() => frame.items.map((it) => ({
    // A known size and known handles (mid-left in, mid-right out), so React Flow never measures a card: it
    // hides one to measure it when its data changes, forgets measured handles on every new node object (the
    // animation makes one each frame) and draws no edge until it measures again, and drags to NaN without
    // `measured`.
    id: it.id, type: "note", width: it.w, height: it.h, measured: { width: it.w, height: it.h },
    position: offsets[it.id] ? { x: it.x + offsets[it.id].dx, y: it.y + offsets[it.id].dy } : { x: it.x, y: it.y },
    handles: handles(it.w, it.h),
    style: { opacity: it.opacity, pointerEvents: it.leaving ? "none" : undefined },
    data: { ...it.entry, w: it.w, h: it.h, color: G.schema.types[it.entry.node.type].color,
            selected: it.id === selected, connecting: it.id === connectFrom, showRank: filter && filter.kind === "agenda" },
  })), [frame, selected, connectFrom, offsets, filter]);

  // Dragging a card moves it from its place in the layout; the offset is kept (per vault, in the browser)
  // through later layouts until the positions are reset.
  const onNodesChange = (changes) => {
    const moved = changes.filter((c) => c.type === "position" && c.position);
    if (!moved.length) return;
    const base = new Map(frame.items.map((it) => [it.id, it]));
    const next = { ...offsets };
    for (const c of moved) {
      const it = base.get(c.id);
      if (it) next[c.id] = { dx: c.position.x - it.x, dy: c.position.y - it.y };
    }
    setOffsets(next);
    latestOffsets.current = next;
  };
  const latestOffsets = useRef(offsets);
  latestOffsets.current = offsets;
  const saveOffsets = (next) => storage.set(G.vault, "offsets", next);

  const edges = useMemo(() => {
    const colors = { supports: css("--supports"), opposes: css("--opposes"), "blocked-by": css("--blocked") };
    const opacity = new Map(frame.items.map((it) => [it.id, it.opacity]));
    const at = new Map(frame.items.map((it) => [it.id, offsets[it.id] ? { ...it, x: it.x + offsets[it.id].dx, y: it.y + offsets[it.id].dy } : it]));
    return frame.edges.filter((e) => opacity.has(e.from) && opacity.has(e.to)).map(({ edge, from, to, cross, arrowAtEnd }) => {
      const color = colors[edge.rel] || css("--edge");
      const [sourceHandle, targetHandle] = sides(at, from, to);
      return {
        id: edge.id, type: "relation", source: from, target: to, sourceHandle, targetHandle, label: G.schema.relations[edge.rel].label,
        data: { forward: arrowAtEnd }, className: "rel-" + edge.rel + (cross ? " cross" : ""),
        style: { stroke: color, opacity: Math.min(opacity.get(from), opacity.get(to)) },
      };
    });
  }, [frame, offsets]);

  // --- Changing the view ---

  const setFilter = (f) => {
    after.current = { fit: true };
    setFilterUnfolded(new Set());
    setFilterState(f && f.kind ? f : null);
  };

  const toggleFold = (id) => {
    after.current = { anchor: id };
    if (matches) {
      const next = new Set(filterUnfolded);
      if (next.has(id)) next.delete(id); else next.add(id);
      return setFilterUnfolded(next);
    }
    const next = new Set(unf);
    if (next.has(id)) next.delete(id); else next.add(id);
    setUnfolded(next);
  };

  const focusOn = (id) => {
    after.current = { fit: true };
    if (!id) return setTrail([]);
    setUnfolded(new Set(unf).add(id));
    const at = foc ? trail.indexOf(id) : -1;
    if (at >= 0) setTrail(trail.slice(0, at + 1));                                  // back up the trail
    else if (foc && descendants(s, foc).has(id)) setTrail(trail.concat(downPath(s, foc, id).slice(1)));  // deeper
    else setTrail(pathTo(s, id));
    if (id) setSelected(id);
  };

  // Show a note: lift filters hiding it, unfold a path down to it, select and centre it.
  const reveal = (id, g = G, alsoUnfold = []) => {
    const n = g.byId.get(id);
    if (!n) return;
    const old = supersededBy(g).has(id);  // a superseded note is shown by showing superseded notes
    const types = new Set([...hiddenTypes].filter((t) => t !== n.type && !(old && t === "superseded")));
    const proj = project && !n.projects.includes(project) ? "" : project;
    const s2 = structure(g, types, proj);
    if (foc && !(s2.inSet.has(foc) && descendants(s2, foc).has(id))) setTrail([]);
    if (restrict && !restrict(n)) setFilterState(null);  // not on the frontier: back to the whole tree
    const next = new Set(unfolded || defaultUnfolded(g, s2));
    const path = pathTo(s2, id).slice(0, -1).concat(alsoUnfold);
    for (const x of path) next.add(x);
    if (filter) setFilterUnfolded(new Set([...filterUnfolded, ...path]));
    after.current = { center: id };
    setHiddenTypes(types);
    setProject(proj);
    setUnfolded(next);
    setSelected(id);
  };

  const find = (q) => {
    if (!q) return false;
    const n = G.byStem.get(q) || G.nodes.find((x) => x.title === q) ||
      G.nodes.find((x) => x.stem.toLowerCase().includes(q.toLowerCase()));
    if (!n) { setToast({ text: "No note matches “" + q + "”.", error: true }); return false; }
    reveal(n.id);
    return true;
  };

  // --- Changing the tree ---

  const changed = async ({ message, created, unfold }) => {
    const g = await load();
    if (created) {
      const n = g.byId.get(created);
      setToast({ text: "Created " + (n ? n.stem : "the note") + (n && !n.projects.length ? "\nIt is in no project yet." : "") });
      if (n) reveal(n.id, g, unfold ? [unfold] : []);
    } else if (message) {
      setToast({ text: message });
    }
  };

  const unlink = async (e) => {
    const r = G.schema.relations[e.rel];
    if (!confirm("Remove the relation?\n\n" + G.byId.get(e.source).stem + "\n  " + r.label + "\n" + G.byId.get(e.target).stem)) return;
    try {
      await api.unlink(e.id);
      await changed({ message: "Removed." });
    } catch (err) {
      setToast({ text: err.message, error: true });
    }
  };

  const action = async (kind, value, id = selected) => {
    if (kind === "connect") return setConnectFrom(selected);
    if (kind === "priority" || kind === "tick" || kind === "answer" || kind === "order") {
      try {
        if (kind === "tick") await api.tick(value);
        else if (kind === "order") await api.order(value);
        else if (kind === "answer") await api.answer(value.id, value.text);
        else await api.setFields(id, { priority: value });
        await changed({ message: kind === "order" ? (value.length ? "Order saved, in the notebook for the next session."
                                                         : "Back to the default order.") : kind === "tick" ? "Ticked: " + value : kind === "answer"
          ? "Answered " + value.id + ", in the notebook for the next session." : "Priority set to " + value + "." });
      } catch (err) {
        setToast({ text: err.message, error: true });
      }
      return;
    }
    setDialog(kind === "new" ? { kind, here: selected } : { kind, id: selected });
  };

  useEffect(() => {
    const esc = (e) => { if (e.key === "Escape") setConnectFrom(null); };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, []);

  if (!G) return html`<div className="loading">Loading…</div>`;
  const Dialog = dialog && DIALOGS[dialog.kind];
  return html`
    <div className="app">
      <${Toolbar} G=${G} project=${project} hiddenTypes=${hiddenTypes} filter=${filter} setFilter=${setFilter}
        matchCount=${matches ? matches.size : null}
        setProject=${(p) => { after.current = { fit: true }; setProject(p); }}
        toggleType=${(t) => {
          const next = new Set(hiddenTypes);
          if (next.has(t)) next.delete(t); else next.add(t);
          setHiddenTypes(next);
        }}
        onFind=${find}
        onFoldDefault=${() => { after.current = { fit: true }; setUnfolded(null); setFilterUnfolded(new Set()); }}
        onUnfoldAll=${() => {
          after.current = { fit: true };
          const all = new Set(G.nodes.map((n) => n.id));
          if (matches) setFilterUnfolded(all); else setUnfolded(all);
        }}
        onFit=${() => flow.fitView({ padding: 0.12, duration: 250 })}
        onResetPositions=${Object.keys(offsets).length ? () => { setOffsets({}); saveOffsets({}); } : null}
        onNewRoot=${() => setDialog({ kind: "root", project })}
        onOverview=${() => { setSelected(null); setFilter(null); }} />
      <${Breadcrumb} G=${G} path=${foc ? trail : null} onFocus=${focusOn}
        onReset=${() => { after.current = { fit: true }; setTrail([]); setUnfolded(null); }} />
      <main>
        <div className="graph">
          ${matches && !view.nodes.length ? html`<div className="empty muted">No notes match this filter.</div>` : null}
          <${ReactFlow} nodes=${nodes} edges=${edges} nodeTypes=${nodeTypes} edgeTypes=${edgeTypes}
            nodesDraggable=${true} nodeDragThreshold=${4} onNodesChange=${onNodesChange}
            onNodeDragStop=${() => saveOffsets(latestOffsets.current)} panOnDrag=${[0, 1]}
            nodesConnectable=${false} elementsSelectable=${false}
            minZoom=${0.1} maxZoom=${2.5} proOptions=${{ hideAttribution: true }} zoomOnDoubleClick=${false}
            onNodeClick=${(e, node) => {
              if (connectFrom) {
                if (node.id !== connectFrom) setDialog({ kind: "connect", a: connectFrom, b: node.id });
                setConnectFrom(null);
              } else if (e.altKey) { e.preventDefault(); focusOn(node.id); }
              else if (e.ctrlKey || e.metaKey) { e.preventDefault(); toggleFold(node.id); }
              else setSelected(node.id);
            }}
            onPaneClick=${() => { if (!connectFrom) setSelected(null); }}>
            <${Background} gap=${22} size=${1} />
            <${Controls} showInteractive=${false} />
            <${MiniMap} pannable zoomable nodeColor=${(n) => n.data.color} nodeStrokeWidth=${0} />
          </${ReactFlow}>
        </div>
        <${Panel} G=${G} id=${selected} matches=${matches} byRank=${!!filter && filter.kind === "agenda"} onReveal=${reveal} onFocus=${focusOn} onAction=${action} onUnlink=${unlink} />
      </main>
      ${connectFrom ? html`
        <div className="banner">Click the note to connect “${G.byId.get(connectFrom).title}” to.
          <button onClick=${() => setConnectFrom(null)}>Cancel</button></div>` : null}
      ${toast ? html`<div className=${"toast" + (toast.error ? " error" : "")}>${toast.text}</div>` : null}
      ${Dialog ? html`<${Dialog} G=${G} ...${dialog} onClose=${() => setDialog(null)} onDone=${changed} />` : null}
    </div>`;
}

createRoot(document.getElementById("root")).render(html`<${ReactFlowProvider}><${App} /></${ReactFlowProvider}>`);
