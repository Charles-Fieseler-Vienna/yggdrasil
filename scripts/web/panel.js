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

// A question waiting on the user, with a box to answer it: `ygg answer ID -m TEXT`, in the notebook, where
// the next session finds it.
function Ask({ q, link, onAction, here }) {
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const names = (key, label) => (q[key] && q[key].length ? html`<span className="muted"> · ${label} ${q[key].map((x, i) =>
    html`${i ? ", " : ""}${link(x.id, x.stem)}`)}</span>` : null);
  const send = async () => {
    setSending(true);
    await onAction("answer", { id: q.id, text: text.trim() });
    setSending(false);
  };
  return html`
    <div className="ask">
      <p><span className="ask-badge">?</span> <b>${q.question}</b></p>
      ${here ? html`<p className="muted">${q.id}: ${q.blocks ? "the work on this note waits for your answer" : "about this note"}</p>`
        : html`<p className="muted">${q.id}, ${q.when}${q.context ? ": " + q.context : ""}${names("on", "on")}${names("blocks", "blocks")}</p>`}
      <textarea value=${text} placeholder="Your answer, and why" onInput=${(e) => setText(e.target.value)} />
      <div className="ask-actions"><span className="muted">goes into the notebook</span>
        <button disabled=${!text.trim() || sending} onClick=${send}>Answer</button></div>
    </div>`;
}

// The agent's list, most important first, as the session briefing gives it: the notes that can be started,
// numbered, then the blocked ones. Dragging a row (or ↑ ↓) reorders it; saving runs `ygg order` with the
// numbered notes, a notebook entry that puts them first.
const plain = (why) => why.replace(/\[\[|\]\]/g, "");

export function Agenda({ G, link, onAction }) {
  const base = G.agenda.filter((id) => G.byId.get(id).rank);
  const stuck = G.agenda.filter((id) => !G.byId.get(id).rank);
  const [draft, setDraft] = useState(null);  // {from: the order it was made from, ids}
  const [dragged, setDragged] = useState(null);
  const ids = draft && draft.from === base.join() ? draft.ids : base;
  const changed = ids.join() !== base.join();
  const move = (from, to) => {
    if (to < 0 || to >= ids.length || from === to) return;
    const next = ids.slice();
    next.splice(to, 0, next.splice(from, 1)[0]);
    setDraft({ from: base.join(), ids: next });
  };
  const order = G.agendaOrder;
  const placed = order ? base.filter((id) => order.stems.includes(G.byId.get(id).stem)).length : 0;
  const row = (id, i) => {
    const n = G.byId.get(id);
    return html`<li key=${id} className=${"agenda-item" + (i !== null && dragged === i ? " dragged" : "") + (i === null ? " blocked" : "")}
        draggable=${i !== null} onDragStart=${(e) => { e.dataTransfer.effectAllowed = "move"; setDragged(i); }}
        onDragEnd=${() => setDragged(null)}
        onDragOver=${(e) => { if (i !== null && dragged !== null) { e.preventDefault(); if (dragged !== i) { move(dragged, i); setDragged(i); } } }}>
      ${i !== null ? html`<span className="grip" title="Drag to reorder">⠿</span>` : null}
      <span className="rank">${i === null ? "–" : i + 1 + "."}</span>
      <div className="agenda-text"><div>${link(id, n.title)}</div>
        <div className="muted">${n.agenda.map(plain).join(", ")}
        ${n.status !== "done" ? html` · priority <select className="inline" value=${n.meta.priority || "normal"} title="priority"
            onChange=${(e) => onAction("priority", e.target.value, id)}>
          ${G.schema.priorities.map((v) => html`<option key=${v} value=${v}>${v}</option>`)}</select>` : null}</div></div>
      ${i !== null ? html`<span className="moves">
        <button title="Up" disabled=${i === 0} onClick=${() => move(i, i - 1)}>↑</button>
        <button title="Down" disabled=${i === ids.length - 1} onClick=${() => move(i, i + 1)}>↓</button></span>` : null}
    </li>`;
  };
  return html`
    <p className="muted agenda-order">${placed
      ? html`The first ${placed} in the order you set on ${order.when}; the rest in the default order. `
      : "In the default order: answered by you, in progress, high priority, named in the last handoff. "}
      ${ids.length > 1 ? "Drag ⠿ (or ↑ ↓) to reorder." : null}</p>
    <ol className="match-list agenda">${ids.map((id, i) => row(id, i))}</ol>
    ${changed || placed ? html`<div className="agenda-actions">${changed ? html`
      <span className="muted">goes into the notebook</span>
      <button onClick=${() => setDraft(null)}>Cancel</button>
      <button className="primary" onClick=${() => { onAction("order", ids); setDraft(null); }}>Save order</button>` : html`
      <button onClick=${() => onAction("order", [])} title="Drop your order">Default order</button>`}
    </div>` : null}
    ${stuck.length ? html`<p className="muted agenda-order">Blocked: not started until what blocks them is done or answered.</p>
      <ol className="match-list agenda">${stuck.map((id) => row(id, null))}</ol>` : null}`;
}

// With nothing selected and no filter: where the work stands, as the agent is told it (the same lists the
// SessionStart briefing and `ygg report` give), and the briefing itself.
function Overview({ G, onReveal, onAction }) {
  const [o, setO] = useState(null);
  const [error, setError] = useState(null);
  const [ticking, setTicking] = useState(new Set());  // to-dos ticked here, until the notebook says so
  useEffect(() => {
    let live = true;
    api.overview().then((r) => live && (setO(r), setError(null))).catch((e) => live && setError(e.message));
    return () => { live = false; };
  }, [G.version]);
  if (error) return html`<aside className="panel"><p className="muted">${error}</p></aside>`;
  if (!o) return html`<aside className="panel"><p className="muted">Loading…</p></aside>`;
  const link = (id, stem) => (id ? html`<a onClick=${() => onReveal(id)}>${stem}</a>` : stem);
  const section = (title, count, body) => html`<section className="overview-part"><h3>${title}${count === null ? "" : " (" + count + ")"}</h3>${body}</section>`;
  return html`
    <aside className="panel overview">
      <h2>Where things stand</h2>
      ${o.asks.length ? section("Waiting on you", o.asks.length, html`${o.asks.map((q) =>
        html`<${Ask} key=${q.id} q=${q} link=${link} onAction=${onAction} />`)}`) : null}
      ${o.answered.length ? section("Answered since the last handoff", o.answered.length, html`
        <ul className="entries">${o.answered.map((q) => html`<li key=${q.id}><b>${q.question}</b><br />
          <span className="muted">${q.answered || ""}</span> ${q.answer}</li>`)}</ul>
        <p className="muted">The next session is told these, and acts on them.</p>`) : null}
      ${section("What the agent sees first", G.agenda.length, G.agenda.length
        ? html`<${Agenda} G=${G} link=${link} onAction=${onAction} />`
        : html`<p className="muted">Nothing in progress, at high priority or named in the last handoff.
          Set a note's priority to high to put it here.</p>`)}
      ${o.todos.length ? section("To do, from the notebook", o.todos.length, html`
        <ul className="todos">${o.todos.slice().reverse().map((t) => html`
          <li key=${t.entry + ":" + t.text}><label><input type="checkbox" checked=${ticking.has(t.entry + ":" + t.text)}
            onChange=${() => { setTicking(new Set(ticking).add(t.entry + ":" + t.text)); onAction("tick", t.text); }} />
            ${t.text}</label> <span className="muted">${t.when.slice(0, 10)}</span></li>`)}</ul>`) : null}
      ${o.issues.length ? section("Open issues", o.issues.length, html`${o.issues.map((i) => html`
        <div key=${i.id} className="issue">
          <p><span className="issue-badge">!</span> <b>${i.id}</b> ${i.title}</p>
          <p className="muted">${i.notes.length} note${i.notes.length === 1 ? "" : "s"} still to judge${i.judged ? ", " + i.judged + " judged" : ""}</p>
          <ul>${i.notes.slice(0, 12).map((n) => html`<li key=${n.stem}>${link(n.id, n.stem)}</li>`)}
            ${i.notes.length > 12 ? html`<li className="muted">and ${i.notes.length - 12} more</li>` : null}</ul>
        </div>`)}`) : null}
      ${o.runs || o.needs_action.length ? section("Runs", null, html`
        ${o.runs ? html`<p>${o.runs.replace(" `ygg runs` lists them.", "")}</p>` : null}
        ${o.needs_action.length ? html`<ul>${o.needs_action.map((x, i) => html`<li key=${i}>${x.replace(/^- /, "")}</li>`)}</ul>` : null}`) : null}
      ${o.distil ? section("In the notebook, not yet in the tree", null, html`<p>${o.distil.replace(/^- /, "")}</p>`) : null}
      ${o.handoff ? section("Last handoff, " + o.handoff.when, null, html`
        <div className="markdown" onClick=${(e) => {
          const a = e.target.closest("a.wikilink");
          const target = a && G.byStem.get(a.dataset.stem);
          if (target) onReveal(target.id);
        }} dangerouslySetInnerHTML=${{ __html: renderBody(o.handoff.text) }} />`) : null}
      ${o.entries.length ? section("Recent notebook entries", null, html`
        <ul className="entries">${o.entries.map((e, i) => html`<li key=${i}><span className="muted">${e.when}${e.tag ? " · " + e.tag : ""}</span><br />${e.first}</li>`)}</ul>`) : null}
      <details className="briefing">
        <summary>The agent's briefing at session start, word for word</summary>
        <pre>${o.briefing}</pre>
      </details>
      <p className="muted hint">Select a note to see it here. Ctrl-click (or Cmd-click) a note to fold or unfold what is under
        it; alt-click (or Focus) to show only that note and what is under it.</p>
    </aside>`;
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

export function Panel({ G, id, matches, byRank, onReveal, onFocus, onAction, onUnlink }) {
  const n = id && G.byId.get(id);
  const [body, setBody] = useState({ id: null, html: "" });
  useEffect(() => {
    if (!n) return;
    let live = true;
    api.note(n.id).then((r) => live && setBody({ id: n.id, html: renderBody(r.body) }))
      .catch((e) => live && setBody({ id: n.id, html: escapeHtml(e.message) }));
    return () => { live = false; };
  }, [id, G.version]);

  if (!n && matches && byRank) return html`
    <aside className="panel overview"><h3>What the agent sees first (${G.agenda.length})</h3>
      <${Agenda} G=${G} link=${(id, title) => html`<a onClick=${() => onReveal(id)}>${title}</a>`} onAction=${onAction} /></aside>`;
  if (!n && matches) return html`<${MatchList} G=${G} matches=${matches} onReveal=${onReveal} />`;
  if (!n) return html`<${Overview} G=${G} onReveal=${onReveal} onAction=${onAction} />`;
  const spec = G.schema.types[n.type];
  const done = n.status === "done";
  const priority = done ? n.meta.priority : html`
    <select className="inline" value=${n.meta.priority || "normal"} onChange=${(e) => onAction("priority", e.target.value)}
            title="high: listed to the agent at the start of each session; none: off the frontier">
      ${G.schema.priorities.map((v) => html`<option key=${v} value=${v}>${v}</option>`)}
    </select>`;
  const fields = [["status", n.status], ["priority", priority], ["agent", n.agenda.length ? "sees it first (" + n.agenda.join(", ") + ")" : null],
                  ["confidence", n.confidence], ["outcome", n.outcome],
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
      ${n.issues.length ? html`<div className="issues">${n.issues.map((i) => html`
        <p key=${i.id}><span className="issue-badge">!</span> <b>${i.id}</b> ${i.title}: to judge whether this still
          holds (rerun and supersede, or note it unaffected in the notebook with the issue id).</p>`)}</div>` : null}
      ${n.asks.map((q) => html`<${Ask} key=${q.id} q=${q} here=${true} onAction=${onAction} link=${() => null} />`)}
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
