---
name: compress
description: Compress a project's detailed ygg tree into the user's main tree as a few generalizable Questions, Claims and Evidence, mapping notes seeded from the main tree back to their originals. Use when the user wants to bring a project's or phase's results back to the main tree, or to compress a project tree again after more work.
---

# Compressing a project tree

With the user, once the project tree is committed. Follow the `ygg:tree` skill (all writes through `ygg`).

The main tree is the one `ygg main` prints; if none is set, ask the user which it is and set it with
`ygg main PATH`. Run `ygg compress PATH/TO/project/tree --dry-run` (from anywhere: it records into the main
tree) to read the outline with the user, then without `--dry-run` to record the tree as a Source at its
commit. Then write the compressed nodes, in the main tree (`cd "$(ygg main)"`, or `--vault "$(ygg main)"`): about one Question per figure, one Claim per one to three panels, each Claim
with its own Evidence derived from the tree Source and the Dataset. Keep generalizable results, dead ends and
open questions; leave narrow methods in the project tree. Add roots with `ygg set PROJECT --add-root NOTE`.
The outline's **Papers** list says which papers already have a Source in the main tree (derive from that one;
never make a second) and which lack a Zotero key or DOI. **Seeded from this tree** lists the notes copied
from the main tree with what the project added under them: write those against the original notes, not new
copies. **Out of scope there** and **In no project there** list notes the project left for elsewhere,
often from brainstorms: with the user, move each into the main tree as a new note (the project's stays), or
leave it. On a second compression of the same tree, **Since the last compression** lists only the new and
changed notes, relations and notebook entries, and the outline marks them.

Close with a notebook entry in the main tree (`ygg log --tag compress --body -`, on stdin) listing what was
compressed, what was left in the project tree and why, then `ygg check`. Commit only when the user asks.
