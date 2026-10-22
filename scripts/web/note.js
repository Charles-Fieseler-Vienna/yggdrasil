// A note's card on the graph. Fill and border come from its type; the flag (gap, open, weak, out)
// restyles the border; badges mark a note under an open issue (top right), a high-priority one (top left) and one with a question
// waiting on the user (bottom right); a folded card looks stacked and says what it hides. Under a filter, the
// notes shown only as context for a match are faded.
import { Handle, Position } from "@xyflow/react";
import { html } from "./html.js";

export function NoteCard({ data }) {
  const { node, folded, hidden, color, selected, connecting, from } = data;
  const classes = ["note", node.flag ? "flag-" + node.flag : "", folded && hidden.count ? "folded" : "",
                   hidden.gaps ? "hidden-gaps" : "", selected ? "selected" : "", connecting ? "connecting" : "",
                   node.status === "done" ? "done" : "", node.superseded ? "superseded" : "", node.meta.priority === "none" ? "prio-none" : "", data.match ? "" : "context"].filter(Boolean).join(" ");
  const gaps = hidden.gaps ? " · " + hidden.gaps + (hidden.gaps === 1 ? " gap" : " gaps") : "";
  return html`
    <div className=${classes} style=${{ "--type": color, width: data.w, height: data.h }}
         title=${node.stem + "\nCtrl-click: fold or unfold · Alt-click: focus on it"}>
      <${Handle} type="target" position=${Position.Left} isConnectable=${false} />
      <div className="note-title">${node.title}</div>
      ${from.length ? html`<div className="note-from" title=${"Done notes above it:\n" + from.map((p) => p.stem).join("\n")}>
        after ${from[0].title}${from.length > 1 ? " +" + (from.length - 1) : ""}</div>` : null}
      ${node.meta.priority === "high" && node.status !== "done" ? html`<span className="prio-badge" title="high priority">▲</span>` : null}
      ${node.issues.length ? html`<span className="issue-badge" title=${node.issues.map((i) => i.id + ": " + i.title).join("\n")}>!</span>` : null}
      ${node.asks.length ? html`<span className="ask-badge" title=${"Waiting on you:\n" + node.asks.map((q) => q.id + ": " + q.question).join("\n")}>?</span>` : null}
      ${folded && hidden.count ? html`<div className="note-badge">▸ ${hidden.count} hidden${gaps}</div>` : null}
      <${Handle} type="source" position=${Position.Right} isConnectable=${false} />
    </div>`;
}

export const nodeTypes = { note: NoteCard };
