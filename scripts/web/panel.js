// The side panel: the selected note's fields, actions, relations and rendered body.
import { useEffect, useState } from "react";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { api } from "./api.js";
import { html } from "./html.js";

const WIKILINK = /\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]/g;
const FLAG_TEXT = { gap: "gap: needs work", open: "open or in progress", weak: "weak",
                    out: "out of scope: moves out at compression" };

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function renderBody(md) {
  const linked = md.replace(WIKILINK, (m, stem, alias) =>
    '<a class="wikilink" data-stem="' + escapeHtml(stem.trim()) + '">' + escapeHtml(alias || stem) + "</a>");
  return DOMPurify.sanitize(marked.parse(linked));
}

// With nothing selected and a filter on: its matches, most recently changed first.
function MatchList({ G, matches, onReveal }) {
  const list = [...matches].map((id) => G.byId.get(id))
    .sort((a, b) => String(b.meta.dateModified || "").localeCompare(String(a.meta.dateModified || "")));
  return html`
    <aside className="panel">
      <h3>${list.length} ${list.length === 1 ? "match" : "matches"}, most recently changed first</h3>
      <ul className="match-list">
        ${list.map((n) => html`
          <li key=${n.id}>
            <span className="type-chip" style=${{ background: G.schema.types[n.type].color }}>${G.schema.types[n.type].name[0]}</span>
            <a onClick=${() => onReveal(n.id)}>${n.title}</a>
            <span className="when muted">${String(n.meta.dateModified || "").slice(0, 10)}</span>
          </li>`)}
      </ul>
    </aside>`;
}

export function Panel({ G, id, matches, onReveal, onFocus, onAction, onUnlink }) {
  const n = id && G.byId.get(id);
  const [body, setBody] = useState({ id: null, html: "" });
  useEffect(() => {
    if (!n) return;
    let live = true;
    api.note(n.id).then((r) => live && setBody({ id: n.id, html: renderBody(r.body) }))
      .catch((e) => live && setBody({ id: n.id, html: escapeHtml(e.message) }));
    return () => { live = false; };
  }, [id, G.version]);

  if (!n && matches) return html`<${MatchList} G=${G} matches=${matches} onReveal=${onReveal} />`;
  if (!n) {
    return html`<aside className="panel"><p className="muted">
      Select a note to see it here. Ctrl-click (or Cmd-click) a note to fold or unfold what is under it;
      alt-click (or Focus) to show only that note and what is under it.</p></aside>`;
  }
  const spec = G.schema.types[n.type];
  const done = n.status === "done";
  const fields = [["status", n.status], ["priority", n.meta.priority], ["confidence", n.confidence], ["outcome", n.outcome],
                  ["flag", FLAG_TEXT[n.flag]], ["projects", n.projects.join(", ") || "none"],
                  ...["zotero", "doi", "citekey", "run", "tree", "location", "origin"].map((k) => [k, n.meta[k]]), ["file", n.file]];
  const relations = G.edges.filter((e) => e.source === n.id || e.target === n.id);
  const obsidian = "obsidian://open?vault=" + encodeURIComponent(G.vault) + "&file=" + encodeURIComponent(n.file);
  const clickBody = (e) => {
    const a = e.target.closest("a.wikilink");
    const target = a && G.byStem.get(a.dataset.stem);
    if (target) onReveal(target.id);
  };
  return html`
    <aside className="panel">
      <span className="type-chip" style=${{ background: spec.color }}>${spec.name}</span>
      <h2>${n.title}</h2>
      <dl className="fields">
        ${fields.filter(([, v]) => v).map(([k, v]) => html`<dt key=${k + "t"}>${k}</dt><dd key=${k}>${v}</dd>`)}
      </dl>
      <div className="actions">
        <button onClick=${() => onFocus(n.id)} title="Show only this note and what is under it">Focus</button>
        <button onClick=${() => onAction("connect")}>Connect to…</button>
        <button onClick=${() => onAction("new")}>New note here</button>
        ${done ? null : html`<button onClick=${() => onAction("set")}>Set…</button>`}
        ${done ? null : html`<button onClick=${() => onAction("done")}>Mark done…</button>`}
        <a href=${obsidian}>Open in Obsidian</a>
        ${n.meta.zotero ? html`<a href=${"zotero://select/library/items/" + n.meta.zotero}>Open in Zotero</a>` : null}
        ${n.meta.doi ? html`<a href=${"https://doi.org/" + n.meta.doi} target="_blank" rel="noreferrer">DOI</a>` : null}
      </div>
      <h3>Relations</h3>
      <ul className="relations">
        ${relations.length ? null : html`<li className="muted">none</li>`}
        ${relations.map((e) => {
          const out = e.source === n.id;
          const other = G.byId.get(out ? e.target : e.source);
          const r = G.schema.relations[e.rel];
          const frozen = done || other.status === "done";
          return html`
            <li key=${e.id}>
              <span className="rel">${out ? r.label : r.complement}</span>
              <a onClick=${() => onReveal(other.id)}>${other.stem}</a>
              <button className="danger" disabled=${frozen} onClick=${() => onUnlink(e)}
                      title=${frozen ? "Relations touching a done note cannot be removed" : "Remove this relation"}>×</button>
            </li>`;
        })}
      </ul>
      <h3>Note</h3>
      <div className="markdown" onClick=${clickBody}
           dangerouslySetInnerHTML=${{ __html: body.id === n.id ? body.html : "" }} />
    </aside>`;
}
