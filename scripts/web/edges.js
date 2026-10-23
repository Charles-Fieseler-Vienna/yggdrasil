// A relation's edge: a curve from parent (left) to child (right), its label, and an arrowhead
// on the curve itself pointing the relation's way. Arrowheads at the ends would all pile up on
// a parent with many children, since most relations point from child to parent.
import { BaseEdge } from "@xyflow/react";
import { html } from "./html.js";

const LABEL_AT = 0.4, ARROW_AT = 0.68, ARROW = 9;

const OUT = { left: [-1, 0], right: [1, 0], top: [0, -1], bottom: [0, 1] };

// A cubic curve leaving s by side sp and entering t by side tp: right to left as React Flow draws them,
// bottom to top between neighbours in a column, and a loop out to the right between cards further apart.
function curve(sx, sy, sp, tx, ty, tp) {
  const dx = tx - sx, dy = Math.abs(ty - sy);
  const d = sp === "right" && tp === "left" ? (dx >= 0 ? 0.5 * dx : 0.25 * 25 * Math.sqrt(-dx))
          : sp === tp ? 40 + 0.15 * dy : 0.4 * dy;  // under half the gap, so the curve never doubles back
  const P = [[sx, sy], [sx + d * OUT[sp][0], sy + d * OUT[sp][1]], [tx + d * OUT[tp][0], ty + d * OUT[tp][1]], [tx, ty]];
  const at = (t) => {
    const u = 1 - t, w = [u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t];
    return [0, 1].map((k) => w.reduce((a, wi, i) => a + wi * P[i][k], 0));
  };
  const slope = (t) => {
    const u = 1 - t, w = [3 * u * u, 6 * u * t, 3 * t * t];
    return [0, 1].map((k) => w.reduce((a, wi, i) => a + wi * (P[i + 1][k] - P[i][k]), 0));
  };
  return { path: `M${sx},${sy} C${P[1]} ${P[2]} ${tx},${ty}`, at, slope };
}

export function RelationEdge({ id, sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition, label, style, data }) {
  const c = curve(sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition);
  // between neighbours in a column the gap is short: the arrowhead mid-gap, the label beside it
  const short = sourcePosition !== targetPosition && (sourcePosition === "top" || sourcePosition === "bottom");
  const [ax, ay] = c.at(short ? 0.5 : ARROW_AT);
  const [lx, ly] = short ? [ax + 12 + 3 * String(label).length, ay] : c.at(LABEL_AT);
  const [vx, vy] = c.slope(short ? 0.5 : ARROW_AT);
  const angle = Math.atan2(vy, vx) * 180 / Math.PI + (data.forward ? 0 : 180);
  return html`
    <${BaseEdge} id=${id} path=${c.path} style=${style} label=${label} labelX=${lx} labelY=${ly}
                 labelBgPadding=${[4, 2]} labelBgBorderRadius=${3} />
    <path d=${`M${ARROW},0 L${-ARROW * 0.6},${-ARROW * 0.6} L${-ARROW * 0.6},${ARROW * 0.6} Z`}
          transform=${`translate(${ax},${ay}) rotate(${angle})`}
          style=${{ fill: style.stroke, opacity: style.opacity }} className="relation-arrow" />`;
}

export const edgeTypes = { relation: RelationEdge };
