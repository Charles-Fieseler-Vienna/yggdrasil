# TODO

Known small issues, kept for later (from the review of 2026-10-22).

- The session hook searches three folders down from the working directory, so a session started in `~`
  finds the main tree and announces it. Search downwards only inside a git repository.
- The web app loads React and React Flow from esm.sh, so it does not work offline. Vendor the few modules.
- Decide whether the main tree keeps a notebook (brainstorm decisions, compression notes); DESIGN.md is vague.
- Every `ygg` command rebuilds the graph from all files. Fine at hundreds of notes; watch it in big project
  trees.
- Not tested: the Discourse Graph Obsidian plugin and `ygg` writing `relations.json` at the same time (does
  the plugin overwrite it from memory?).
- Zotero lookups need the local Zotero app; on machines without it, paper steps fall back to DOIs.
- No plugin icon.
- A seeded copy goes stale when its main-tree original changes later; `ygg seed` again reuses the copy and
  does not say so. It could report originals changed since the commit in the copy's `origin`.
- `ygg watch` ends with the session that started it; nothing outside a session waits on runs.
