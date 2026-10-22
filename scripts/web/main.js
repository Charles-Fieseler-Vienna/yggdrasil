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
  const onPlaced = (to) => {
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
    // A known size, so React Flow never hides a card to measure it again when its data changes.
    id: it.id, type: "note", position: { x: it.x, y: it.y }, width: it.w, height: it.h,
    style: { opacity: it.opacity, pointerEvents: it.leaving ? "none" : undefined },
    data: { ...it.entry, w: it.w, h: it.h, color: G.schema.types[it.entry.node.type].color,
            selected: it.id === selected, connecting: it.id === connectFrom },
  })), [frame, selected, connectFrom]);

  const edges = useMemo(() => {
    const colors = { supports: css("--supports"), opposes: css("--opposes") };
    const opacity = new Map(frame.items.map((it) => [it.id, it.opacity]));
    return frame.edges.filter((e) => opacity.has(e.from) && opacity.has(e.to)).map(({ edge, from, to, cross, arrowAtEnd }) => {
      const color = colors[edge.rel] || css("--edge");
      return {
        id: edge.id, type: "relation", source: from, target: to, label: G.schema.relations[edge.rel].label,
        data: { forward: arrowAtEnd }, className: "rel-" + edge.rel + (cross ? " cross" : ""),
        style: { stroke: color, opacity: Math.min(opacity.get(from), opacity.get(to)) },
      };
    });
  }, [frame]);

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
    if (kind === "priority" || kind === "tick" || kind === "answer") {
      try {
        if (kind === "tick") await api.tick(value);
        else if (kind === "answer") await api.answer(value.id, value.text);
        else await api.setFields(id, { priority: value });
        await changed({ message: kind === "tick" ? "Ticked: " + value : kind === "answer"
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
        onNewRoot=${() => setDialog({ kind: "root", project })}
        onOverview=${() => { setSelected(null); setFilter(null); }} />
      <${Breadcrumb} G=${G} path=${foc ? trail : null} onFocus=${focusOn}
        onReset=${() => { after.current = { fit: true }; setTrail([]); setUnfolded(null); }} />
      <main>
        <div className="graph">
          ${matches && !view.nodes.length ? html`<div className="empty muted">No notes match this filter.</div>` : null}
          <${ReactFlow} nodes=${nodes} edges=${edges} nodeTypes=${nodeTypes} edgeTypes=${edgeTypes}
            nodesDraggable=${false} nodesConnectable=${false} elementsSelectable=${false}
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
        <${Panel} G=${G} id=${selected} matches=${matches} onReveal=${reveal} onFocus=${focusOn} onAction=${action} onUnlink=${unlink} />
      </main>
      ${connectFrom ? html`
        <div className="banner">Click the note to connect “${G.byId.get(connectFrom).title}” to.
          <button onClick=${() => setConnectFrom(null)}>Cancel</button></div>` : null}
      ${toast ? html`<div className=${"toast" + (toast.error ? " error" : "")}>${toast.text}</div>` : null}
      ${Dialog ? html`<${Dialog} G=${G} ...${dialog} onClose=${() => setDialog(null)} onDone=${changed} />` : null}
    </div>`;
}

createRoot(document.getElementById("root")).render(html`<${ReactFlowProvider}><${App} /></${ReactFlowProvider}>`);
