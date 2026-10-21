---
name: handoff
description: Hand off a project's state at the end of a session (distil the lab notebook into the ygg tree, then append a handoff entry), or catch up at the start of one (read the last handoff, what changed since, and what is running, open or weak). Use when the user says hand off, wrap up, stopping for now, where was I, catch me up, or what's the state of a project.
---

# Handoffs in a ygg tree

A project has three layers (see `${CLAUDE_PLUGIN_ROOT}/DESIGN.md`, Notebook): the lab notebook `NOTEBOOK.md` (raw, dated,
append-only), its tree (the cleaned-up graph), and, at the end of a phase, the compressed nodes in
the main tree. A handoff keeps the first two in step and leaves a note for the next session. Run `ygg` in the
project's tree (the folder with `ygg.json`, e.g. `research/tree`), or pass `--vault PATH`.

## Handing off ("hand off", "wrap up", "stopping here")

1. **Read what happened.** `ygg report --since handoff` lists the notebook entries and changed notes since the
   last handoff; read those entries in full in `NOTEBOOK.md`, and recall this session's work. Check the
   project repository with `git status` and `git log` since the last handoff.
2. **Distil the notebook into the tree.** Propose a short list to the user, then write what they approve
   with `ygg` (following the `ygg:tree` skill):
   - a run launched: a Source with `--run repo@commit:path` (a real commit; if the code was uncommitted, say
     so instead) and its Evidence, `--status in-progress`; job IDs and output paths go in the Source's
     `--add-data`;
   - a result in: fill in the Evidence and `ygg done` it, with the outcome; failed and ambiguous ones too;
   - a decision that held: a Claim (claims about methods are claims) with its Evidence; a dead end: Evidence
     with outcome `failed`, saying what would make it worth retrying;
   - a new question: a Question with `follows-from`.
   Leave in the notebook what is still a hunch. Don't force every entry into a node.
3. **Set priorities.** `ygg set NOTE --priority high` on the one to three things that should happen next;
   lower ones that went cold (`--priority low`).
4. **Write the handoff entry** with `ygg log --handoff --body FILE`, short and concrete:
   - where things stand, in two or three sentences;
   - what is running: job IDs, where output will land, when it should finish;
   - next steps, each linking its node (`[[QUE - ...]]`);
   - loose state: uncommitted code, unmerged branches, scratch paths, anything only this session knows.
   Don't repeat what the nodes already say; link them.
5. `ygg check`, then tell the user what was distilled and show the handoff entry. Commit only if asked.

## Catching up ("where was I", "catch me up")

1. `ygg report --since handoff` (add `--project P` in a tree with several projects), and read the last
   handoff entry and everything after it in `NOTEBOOK.md`.
2. `git log` in the project repository since the handoff date.
3. For each run the handoff or the in-progress Evidence names, check whether it finished: the job (e.g.
   `squeue`/`sacct` if on the cluster) or its output path. Don't assume.
4. Brief the user in a few lines: what was running and its state now; the next steps from the handoff and the
   high-priority notes; what changed since; anything weak or blocked worth knowing. Suggest the web app
   (`ygg serve`, with the project selected and the In progress or Not done filter) for the picture.

## During a session

When working in a project, append decisions, dead ends and surprises to the notebook as they happen with
`ygg log "..." --tag decision` (or `dead-end`, `run`, `idea`). Never edit or reorder past entries; correct
one with a new entry.
