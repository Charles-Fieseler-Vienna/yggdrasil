// Dialogs for changing the tree. Each offers only valid choices; the server still runs the
// CLI's checks, and its refusal is shown in the dialog.
import { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { validRelations, titleProblem } from "./graph.js";
import { html } from "./html.js";

function Modal({ title, okText, onSubmit, onClose, children, check }) {
  const ref = useRef(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { ref.current.showModal(); }, []);
  const submit = async (e) => {
    e.preventDefault();
    const problem = check && check();
    if (problem) return setError(problem);
    setBusy(true);
    try {
      await onSubmit();
      onClose();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };
  return html`
    <dialog ref=${ref} onClose=${onClose} onCancel=${onClose}>
      <form onSubmit=${submit}>
        <h3>${title}</h3>
        ${children}
        <p className="error">${error}</p>
        <menu>
          <button type="button" onClick=${onClose}>Cancel</button>
          <button type="submit" className="primary" disabled=${busy}>${okText}</button>
        </menu>
      </form>
    </dialog>`;
}

function Field({ label, children }) {
  return html`<label className="field"><span>${label}</span>${children}</label>`;
}

function Choices({ items, value, onChange }) {
  return html`<div className="choices">
    ${items.map((it, i) => html`
      <label key=${i} className="choice">
        <input type="radio" checked=${value === i} onChange=${() => onChange(i)} />${it.text}
      </label>`)}
  </div>`;
}

// What goes in each section of a new note's body (see DESIGN.md, Bodies). The title is only a
// short name, which is also the filename, so it cannot hold "?" or ":"; the body says it in full.
const SECTION_HINTS = {
  Question: "The question in full, as you would ask it.",
  Context: "Why it matters, what prompted it, related results.",
  Claim: "The claim in full, with its qualifications.",
  Rationale: "Why the evidence supports it.",
  Scope: "Where it holds: data, conditions, methods.",
  Purpose: "What this run or investigation set out to test.",
  Method: "What was done; data, models, parameters.",
  Results: "What came out, with numbers.",
  Conclusion: "One to three sentences, readable on their own: what the result means, with effect size, n and Dataset.",
  Caveats: "Missing runs, data limits, anything that bounds the result (or \"none known\").",
  Description: "What it is, and where to find it.",
  Provenance: "Where it came from and how it was made.",
};

// One optional box per section of the type, each with its hint.
function Sections({ names, values, onChange }) {
  return html`<fieldset className="sections">
    <legend>Body <span className="muted">(all optional; fill in now or later in Obsidian)</span></legend>
    ${names.map((name) => html`
      <label key=${name} className="field">
        <span>${name}</span>
        <textarea rows=${2} placeholder=${SECTION_HINTS[name] || ""} value=${values[name] || ""}
                  onChange=${(e) => onChange({ ...values, [name]: e.target.value })} />
      </label>`)}
  </fieldset>`;
}

const phrase = (G, s, rel, t) => s + "  " + G.schema.relations[rel].label + "  " + t;

export function ConnectDialog({ G, a, b, onClose, onDone }) {
  const A = G.byId.get(a), B = G.byId.get(b);
  const exists = (s, rel, t) => G.edges.some((e) => e.source === s && e.target === t && e.rel === rel);
  const items = validRelations(G.schema, A.type, B.type).map((x) => {
    const [s, t] = x.dir === "out" ? [A, B] : [B, A];
    return { rel: x.rel, s, t, text: phrase(G, s.title, x.rel, t.title) };
  }).filter((x) => !exists(x.s.id, x.rel, x.t.id));
  const [choice, setChoice] = useState(0);
  if (!items.length) {
    return html`<${Modal} title="Connect" okText="OK" onClose=${onClose} onSubmit=${async () => {}}>
      <p>No relation is allowed between a ${A.type} and a ${B.type} that is not there already.</p></${Modal}>`;
  }
  return html`
    <${Modal} title="Connect" okText="Connect" onClose=${onClose} onSubmit=${async () => {
      const x = items[choice];
      const r = await api.link({ source: x.s.id, rel: x.rel, target: x.t.id });
      await onDone({ message: r.message });
    }}>
      <${Choices} items=${items} value=${choice} onChange=${setChoice} />
    </${Modal}>`;
}

export function NewNoteDialog({ G, here, onClose, onDone }) {
  const H = G.byId.get(here);
  const types = Object.keys(G.schema.types).filter((t) => validRelations(G.schema, t, H.type).length);
  const [type, setType] = useState(types.includes("question") ? "question" : types[0]);
  const [title, setTitle] = useState("");
  const [choice, setChoice] = useState(0);
  const [confidence, setConfidence] = useState("low");
  const [sections, setSections] = useState({});
  const spec = G.schema.types[type];
  const newName = "the new " + spec.name.toLowerCase();
  const rels = validRelations(G.schema, type, H.type).map((x) => ({
    ...x, text: x.dir === "out" ? phrase(G, newName, x.rel, H.title) : phrase(G, H.title, x.rel, newName),
  }));
  const levels = G.schema.confidence[type];
  return html`
    <${Modal} title=${"New note linked to “" + H.title + "”"} okText="Create" onClose=${onClose}
              check=${() => titleProblem(title)} onSubmit=${async () => {
      const x = rels[choice];
      const r = await api.createNote({ type, title: title.trim(), rel: x.rel, other: H.id, direction: x.dir,
                                       confidence: levels ? confidence : null, sections });
      await onDone({ created: r.id, unfold: H.id });
    }}>
      <${Field} label="Type">
        <select value=${type} onChange=${(e) => { setType(e.target.value); setChoice(0); }}>
          ${types.map((t) => html`<option key=${t} value=${t}>${G.schema.types[t].name}</option>`)}
        </select>
      </${Field}>
      <${Field} label="Title: a short name for one idea, also the filename (no ? or :)">
        <input type="text" autoFocus value=${title} onChange=${(e) => setTitle(e.target.value)} />
      </${Field}>
      <${Field} label="Relation"><${Choices} items=${rels} value=${choice} onChange=${setChoice} /></${Field}>
      ${levels ? html`
        <${Field} label="Confidence">
          <select value=${confidence} onChange=${(e) => setConfidence(e.target.value)}>
            ${levels.map((v) => html`<option key=${v} value=${v}>${v}</option>`)}
          </select>
        </${Field}>` : null}
      <${Sections} names=${spec.sections} values=${sections} onChange=${setSections} />
    </${Modal}>`;
}

export function NewRootDialog({ G, project, onClose, onDone }) {
  const [proj, setProj] = useState(project || (G.projects[0] || {}).id || "");
  const [title, setTitle] = useState("");
  const [sections, setSections] = useState({});
  return html`
    <${Modal} title="New root question" okText="Create" onClose=${onClose}
              check=${() => (G.projects.length ? titleProblem(title) : "There is no project; make one with `ygg new project`.")}
              onSubmit=${async () => {
                const r = await api.createNote({ type: "question", title: title.trim(), project: proj, sections });
                await onDone({ created: r.id });
              }}>
      <${Field} label="Project (the question becomes one of its roots)">
        <select value=${proj} onChange=${(e) => setProj(e.target.value)}>
          ${G.projects.map((p) => html`<option key=${p.id} value=${p.id}>${p.title}</option>`)}
        </select>
      </${Field}>
      <${Field} label="Title: a short name for the question, also the filename (no ? or :)">
        <input type="text" autoFocus value=${title} onChange=${(e) => setTitle(e.target.value)} />
      </${Field}>
      <${Sections} names=${G.schema.types.question.sections} values=${sections} onChange=${setSections} />
    </${Modal}>`;
}

export function SetDialog({ G, id, onClose, onDone }) {
  const n = G.byId.get(id);
  const levels = G.schema.confidence[n.type];
  const [status, setStatus] = useState(n.status === "in-progress" ? "in-progress" : "open");
  const [confidence, setConfidence] = useState(n.confidence || "low");
  return html`
    <${Modal} title=${"Set fields of “" + n.title + "”"} okText="Save" onClose=${onClose} onSubmit=${async () => {
      await api.setFields(id, { status, confidence: levels ? confidence : null });
      await onDone({ message: "Saved." });
    }}>
      <${Field} label="Status">
        <select value=${status} onChange=${(e) => setStatus(e.target.value)}>
          ${G.schema.statuses.map((v) => html`<option key=${v} value=${v}>${v}</option>`)}
        </select>
      </${Field}>
      ${levels ? html`
        <${Field} label="Confidence">
          <select value=${confidence} onChange=${(e) => setConfidence(e.target.value)}>
            ${levels.map((v) => html`<option key=${v} value=${v}>${v}</option>`)}
          </select>
        </${Field}>` : null}
    </${Modal}>`;
}

export function DoneDialog({ G, id, onClose, onDone }) {
  const n = G.byId.get(id);
  const [outcome, setOutcome] = useState(G.schema.outcomes[0]);
  return html`
    <${Modal} title=${"Mark “" + n.title + "” done"} okText="Mark done" onClose=${onClose} onSubmit=${async () => {
      await api.markDone(id, { outcome: n.type === "evidence" ? outcome : null });
      await onDone({ message: "Done." });
    }}>
      <p>A done note is frozen: it cannot be edited again, only superseded by a new note.</p>
      ${n.type === "evidence" ? html`
        <${Field} label="Outcome">
          <select value=${outcome} onChange=${(e) => setOutcome(e.target.value)}>
            ${G.schema.outcomes.map((v) => html`<option key=${v} value=${v}>${v}</option>`)}
          </select>
        </${Field}>` : null}
    </${Modal}>`;
}

export const DIALOGS = { connect: ConnectDialog, new: NewNoteDialog, root: NewRootDialog, set: SetDialog, done: DoneDialog };
