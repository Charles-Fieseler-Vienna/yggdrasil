// The toolbar (filters, search, fold controls) and the breadcrumb shown while focused on a note.
import { useState } from "react";
import { html } from "./html.js";

export function Toolbar({ G, project, setProject, hiddenTypes, toggleType, onFind, onFoldDefault, onUnfoldAll,
                          onFit, onNewRoot }) {
  const [query, setQuery] = useState("");
  const find = (value) => {
    if (onFind(value.trim())) setQuery("");
  };
  return html`
    <header className="toolbar">
      <strong className="vault">${G.vault}</strong>
      <select value=${project} onChange=${(e) => setProject(e.target.value)} title="Only this project's notes">
        <option value="">All projects</option>
        ${G.projects.map((p) => html`<option key=${p.id} value=${p.id}>${p.title}</option>`)}
      </select>
      <span className="type-toggles">
        ${Object.entries(G.schema.types).map(([t, spec]) => html`
          <label key=${t} className=${"type-toggle" + (hiddenTypes.has(t) ? " off" : "")}>
            <input type="checkbox" checked=${!hiddenTypes.has(t)} onChange=${() => toggleType(t)} />
            <span className="type-chip" style=${{ background: spec.color }}>${spec.name}</span>
          </label>`)}
      </span>
      <input className="search" list="search-list" placeholder="Find a note…" value=${query}
             onChange=${(e) => {
               setQuery(e.target.value);
               if (G.byStem.has(e.target.value)) find(e.target.value);
             }}
             onKeyDown=${(e) => { if (e.key === "Enter") find(query); }} />
      <datalist id="search-list">
        ${[...G.nodes].sort((a, b) => a.stem.localeCompare(b.stem)).map((n) => html`<option key=${n.id} value=${n.stem} />`)}
      </datalist>
      <button onClick=${onFoldDefault} title="Only the top questions unfolded">Fold to default</button>
      <button onClick=${onUnfoldAll}>Unfold all</button>
      <button onClick=${onFit}>Fit</button>
      <button onClick=${onNewRoot} title="A new question that is a root of a project">New root question</button>
      <span className="legend">
        <span className="flag gap">gap</span><span className="flag open">open</span><span className="flag weak">weak</span>
        <span className="hint">ctrl-click folds · alt-click focuses</span>
      </span>
    </header>`;
}

export function Breadcrumb({ G, path, onFocus, onReset }) {
  if (!path) return null;
  return html`
    <nav className="breadcrumb">
      <button onClick=${() => onFocus(path.length > 1 ? path[path.length - 2] : null)} title="Focus on the note above">
        ↑ Up</button>
      <button onClick=${onReset} title="Show the whole tree again, folded to the default">Reset</button>
      <a onClick=${() => onFocus(null)}>All</a>
      ${path.map((id, i) => html`
        <span key=${id}>
          <span className="sep">›</span>
          ${i === path.length - 1 ? html`<strong>${G.byId.get(id).title}</strong>`
                                  : html`<a onClick=${() => onFocus(id)}>${G.byId.get(id).title}</a>`}
        </span>`)}
    </nav>`;
}
