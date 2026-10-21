// Positions for a view: a tidy tree, left to right, one column per level. Children keep the order
// the view gives them, so unfolding a node only moves what is below it down; nothing reorders.
// A node with several shown parents sits under one of them (see chooseParents); its other edges
// are still drawn. Card heights come from measuring the wrapped title with the card's own font.

export const CARD_W = 240;
const PAD_X = 12, PAD_Y = 9, LINE_H = 17, BADGE_H = 18, FONT = "13px system-ui, -apple-system, 'Segoe UI', sans-serif";
const COL_GAP = 90, ROW_GAP = 14, ROOT_GAP = 36;

const ctx = document.createElement("canvas").getContext("2d");

function lineCount(text, width) {
  ctx.font = FONT;
  let lines = 1, line = "";
  for (const word of text.split(/\s+/)) {
    const next = line ? line + " " + word : word;
    if (ctx.measureText(next).width > width && line) { lines++; line = word; } else line = next;
  }
  return lines;
}

export function cardHeight(title, badge) {
  return PAD_Y * 2 + lineCount(title, CARD_W - PAD_X * 2 - 4) * LINE_H + (badge ? BADGE_H : 0) + 8;  // + the widest flag border
}

// Which shown parent each node sits under. A node keeps the parent it had (prev), so unfolding
// another of its parents never moves it; otherwise it goes under its shallowest shown parent.
function chooseParents(view, prev) {
  const depth = new Map(view.roots.map((r) => [r, 0]));
  const shownParents = new Map();
  const queue = [...view.roots];
  while (queue.length) {
    const id = queue.shift();
    for (const k of view.kids.get(id)) {
      if (!shownParents.has(k)) shownParents.set(k, []);
      shownParents.get(k).push(id);
      if (!depth.has(k)) { depth.set(k, depth.get(id) + 1); queue.push(k); }
    }
  }
  const parent = new Map();
  for (const [k, ps] of shownParents) {
    if (view.roots.includes(k)) continue;
    parent.set(k, prev && ps.includes(prev[k]) ? prev[k] : ps.reduce((a, b) => (depth.get(b) < depth.get(a) ? b : a)));
  }
  return parent;
}

// {id: {x, y, w, h, parent}} for the view's nodes, x and y being the top left corner; prev is the
// last layout, whose parent choices are kept.
export function layoutView(view, prev) {
  const size = new Map(view.nodes.map((v) => [v.node.id, cardHeight(v.node.title, v.hidden.count)]));
  const parent = chooseParents(view, prev && Object.fromEntries(Object.entries(prev).map(([id, p]) => [id, p.parent])));
  const pos = {}, entered = new Set();

  // Lays out id's subtree from `top` down; returns the bottom of what it used.
  const place = (id, depth, top) => {
    entered.add(id);
    const h = size.get(id);
    let y = top, bottom = top, any = false;
    for (const k of view.kids.get(id)) {
      if (parent.get(k) !== id || entered.has(k)) continue;
      bottom = place(k, depth + 1, y);
      y = bottom + ROW_GAP;
      any = true;
    }
    // centred on its children, but never above its own slot
    const ny = any ? Math.max(top, (top + bottom) / 2 - h / 2) : top;
    pos[id] = { x: depth * (CARD_W + COL_GAP), y: ny, w: CARD_W, h, parent: parent.get(id) || null };
    return Math.max(any ? bottom : top, ny + h);
  };

  let top = 0;
  for (const r of view.roots) top = place(r, 0, top) + ROOT_GAP;
  for (const v of view.nodes) if (!entered.has(v.node.id)) top = place(v.node.id, 0, top) + ROOT_GAP;  // a parent cycle
  return pos;
}

// The box around some positions, for fitting the viewport to a layout before it is drawn.
export function bounds(pos) {
  const all = Object.values(pos);
  const x0 = Math.min(...all.map((p) => p.x)), y0 = Math.min(...all.map((p) => p.y));
  const x1 = Math.max(...all.map((p) => p.x + p.w)), y1 = Math.max(...all.map((p) => p.y + p.h));
  return { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
}
