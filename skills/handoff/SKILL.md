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
   - a run whose result matters: a Source with `--run repo@commit:path` (a real commit; if the code was
     uncommitted, say so instead) and its Evidence, citing the run ids in its Method; output folders go in
     the Source's `--add-data`. Most runs never get this far, and that is fine;
   - a result in: fill in the Evidence and `ygg done` it, with the outcome; failed and ambiguous ones too;
   - a decision that held: a Claim (claims about methods are claims) with its Evidence; a dead end: Evidence
     with outcome `failed`, saying what would make it worth retrying;
   - a new question: a Question with `follows-from`.
   Leave in the notebook what is still a hunch. Don't force every entry into a node.
3. **Set priorities.** `ygg set NOTE --priority high` on the one to three things that should happen next;
   lower ones that went cold (`--priority low`, or `none` to take a note off the web app's frontier). Tick
   the to-dos that got done (`ygg tick TEXT`), and check the open issues (`ygg issues`): resolve those fully
   judged, and say in the handoff which notes are still to judge. A decision left for the user is a question
   (`ygg log "context" --ask "..." --on NOTE --blocks NOTE`), not a "your call" in the handoff's prose; act on
   the answers given since the last handoff (the report lists them) and cite their ids.
4. **Write the handoff entry** with `ygg log --handoff --body FILE`, short and concrete:
   - where things stand, in two or three sentences;
   - runs: each one still going, by its run id (`ygg runs` lists them), with where output will land;
     and each ended or dropped run since the last handoff that no node records, by id, with its result in a
     few words ("r261022-41233: no gain, dropped"). That mention is what marks it looked at;
   - next steps, each linking its node (`[[QUE - ...]]`); new small ones without a node as to-dos, task
     lines `- [ ] ...` (the next session sees them counted, and the web app lists them). To-dos already open
     in the notebook carry over by themselves: mention them if they matter, but don't write them again as
     new task lines, or they will be listed twice;
   - loose state: uncommitted code, unmerged branches, scratch paths, anything only this session knows.
   Don't repeat what the nodes already say; link them.
5. `ygg check`, then tell the user what was distilled and show the handoff entry. Commit only if asked.

## Catching up ("where was I", "catch me up")

1. `ygg report --since handoff` (add `--project P` in a tree with several projects), and read the last
   handoff entry and everything after it in `NOTEBOOK.md`.
2. `git log` in the project repository since the handoff date. If the last handoff leaves a decision to the
   user in prose ("your call", "User: decide ...") and `ygg asks` has no question for it, ask it now
   (`ygg log "context" --ask "..." --on NOTE --blocks NOTE`), once, so it waits where the user looks.
3. Check the runs: `ygg runs` lists those still running or not looked at, with their logs, and the report's
   **Needs action** group says which ended, which went quiet, and which Evidence waits for them. Read the
   end of the logs. Cluster jobs and runs on other hosts are not checked: ask the user, don't assume. To be
   told when runs end, start `ygg watch` in the background.
4. Brief the user in a few lines: what was running and its state now; the next steps from the handoff and the
   high-priority notes; questions waiting on the user, and answers to act on; open to-dos and issues; what
   changed since; anything weak or blocked worth knowing.
   Suggest the web app (`ygg serve`: its Overview shows the same, and the Frontier filter the ways forward)
   for the picture.

## During a session

When working in a project, append decisions, dead ends and surprises to the notebook as they happen with
`ygg log "..." --tag decision` (or `dead-end`, `idea`). Log every run you launch, or the user tells you
about: `ygg log "what and why" --pid N --log PATH` (repeat for a sweep; `--job ID` for a cluster job;
`--for NOTE` when it serves an existing note). Cite its run id where its result ends up, or in a notebook
line; give up runs with `ygg drop ID -m "why"` (`--kill` to stop them). Note small next steps as to-dos
(`ygg log "..." --todo "..."`), a problem in data or code as an issue (`--issue --affects NOTE`), and a
decision only the user can make as a question (`--ask "..." --on NOTE --blocks NOTE`; see the `ygg:tree`
skill). Never edit or reorder past entries, except ticking a to-do with `ygg tick`; correct one
with a new entry. The plugin's hook reminds you after commits and launches.
