# TODO

Known small issues, kept for later (from the review of 2026-10-22).

- The web app loads React and React Flow from esm.sh, so it does not work offline. Vendor the few modules.
- Every `ygg` command rebuilds the graph from all files. Fine at hundreds of notes; watch it in big project
  trees.
- Not tested: the Discourse Graph Obsidian plugin and `ygg` writing `relations.json` at the same time (does
  the plugin overwrite it from memory?).
- Zotero lookups need the local Zotero app; on machines without it, paper steps fall back to DOIs.
- No plugin icon.
- A seeded copy goes stale when its main-tree original changes later; `ygg seed` again reuses the copy and
  does not say so. It could report originals changed since the commit in the copy's `origin`.
- `ygg watch` ends with the session that started it; nothing outside a session waits on runs.
- The prose-decision warning misses soft forms such as "once you agree", "if you agree", "with your OK" (trial 17's handoff: "Consider closing [[QUE …]] with a Claim … once you agree three negative lines are enough"). Widening `USER_DECISION_RE` risks noise on ordinary handoffs; decide whether a non-blocking suggestion should become a question (it would then show in the web app's "Waiting on you").
