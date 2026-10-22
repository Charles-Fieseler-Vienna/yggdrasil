// A note's card on the graph. Fill and border come from its type; the flag (gap, open, weak, out)
// restyles the border; a folded card looks stacked and says what it hides. Under a filter, the
// notes shown only as context for a match are faded.
import { Handle, Position } from "@xyflow/react";
import { html } from "./html.js";

export function NoteCard({ data }) {
  const { node, folded, hidden, color, selected, connecting } = data;
  const classes = ["note", node.flag ? "flag-" + node.flag : "", folded && hidden.count ? "folded" : "",
                   hidden.gaps ? "hidden-gaps" : "", selected ? "selected" : "", connecting ? "connecting" : "",
                   node.status === "done" ? "done" : "", data.match ? "" : "context"].filter(Boolean).join(" ");
  const gaps = hidden.gaps ? " · " + hidden.gaps + (hidden.gaps === 1 ? " gap" : " gaps") : "";
  return html`
    <div className=${classes} style=${{ "--type": color, width: data.w, height: data.h }}
         title=${node.stem + "\nCtrl-click: fold or unfold · Alt-click: focus on it"}>
      <${Handle} type="target" position=${Position.Left} isConnectable=${false} />
      <div className="note-title">${node.title}</div>
      ${folded && hidden.count ? html`<div className="note-badge">▸ ${hidden.count} hidden${gaps}</div>` : null}
      <${Handle} type="source" position=${Position.Right} isConnectable=${false} />
    </div>`;
}

export const nodeTypes = { note: NoteCard };
