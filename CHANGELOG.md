# Changelog

ygg has two versions. The **tool version** (`ygg --version`, `.claude-plugin/plugin.json`) follows
semantic versioning for the CLI, web app, skills and hooks. The **tree format** (`spec_version` in each
tree's `ygg.json`) changes only when a tree written by a new ygg could fail the checks of an older one;
`ygg init` upgrades a tree to the current format, and every command warns about a tree in another format.

## 0.5.12 (2026-10-23), tree format 2

- A `run` or `tree` reference given as `owner/repository@commit:path` is refused with the bare form to use.
- `ygg:digest`: make the project right after its root questions, so later notes join it as they are made;
  bodies on stdin.

## 0.5.11 (2026-10-23), tree format 2

- The prose-decision check works line by line: an entry citing one question no longer hides a second
  decision left in prose on another line.
- The session briefing says when the last handoff leaves a decision in prose with no question asked, and
  to ask it now (catch-up sessions rarely load `ygg:handoff`, where that rule lived).

## 0.5.10 (2026-10-23), tree format 2

- A refused `ygg new` says nothing was written (trial 27 took the refusal for a half-made note and tried to
  `ygg done` it).
- `ygg new --project` explains that a note's projects follow from its links.
- The prose-decision warning also catches "(user decision)".

## 0.5.9 (2026-10-23), tree format 2

- `ygg new source` and `ygg new dataset` no longer say "in no project yet: ... make it a root": a Source or
  Dataset joins the projects of the Evidence derived from it (trial 26 took the old line to mean its Sources
  were orphaned).
- The prose-decision warning also catches "needs the user" and "left it for you".

## 0.5.8 (2026-10-23), tree format 2

- `--data` is accepted for `--add-data` (on a new Source there is nothing to add to).
- "done evidence needs an outcome" names the flag and its values.
- The handoff, compress and brainstorm skills pass notebook bodies on stdin, not through a file.

## 0.5.7 (2026-10-23), tree format 2

- `ygg sync` may fill in `dateCreated` and `completedDate` missing from a done note (one made in Obsidian)
  without `check` calling it changed; changing them is still refused.
- `ygg log --on NOTE` without `--ask` points to `--for NOTE`, which ties an entry to a note.
- Tests for `ygg sync` and `ygg schema`.
- `ygg:paper`: never fill in authors, year or venue from memory. Skill examples pass bodies on stdin
  (`--body -`) throughout.

## 0.5.6 (2026-10-23), tree format 2

- The `ygg:tree` skill passes note bodies on stdin (`--body - <<'EOF'`) rather than through fixed scratch
  files such as `/tmp/evd.md`, which sessions and parallel subagents shared and could overwrite.

## 0.5.5 (2026-10-23), tree format 2

- An answer from the user is shown in full up to 1500 characters in the report and the session briefing,
  with a marked cut and a pointer beyond that; `ygg asks --all` prints it whole. It was cut at 300
  characters, silently, which dropped two of three conditions in a real answer.

## 0.5.4 (2026-10-23), tree format 2

- `ygg show` leaves out the Obsidian plugin's `nodeTypeId` and `nodeInstanceId`, which mean nothing to a reader.
- The pre-Bash guard also stops `for` loops polling `pgrep -f PATTERN`, which never break for the same reason
  (a Haiku subagent waited out two such loops in full, trial 22).
- `--outcome inconclusive` is taken as `ambiguous` (asked for twice, trials 21 and 22), and `ygg done` on a
  Question or Claim with `--outcome` says that only Evidence has one.
- `ygg new` says which projects the new note joined, or that it is in none yet (a brainstorm agent believed
  its linked questions were in no project).

## 0.5.3 (2026-10-23), tree format 2

- Compression moves out of the `ygg:tree` skill into its own `ygg:compress` skill, and `ygg:handoff` no
  longer repeats the tree skill's notebook rules: about 1.8 KB less for every session to load.

## 0.5.2 (2026-10-22), tree format 2

- The search for a tree in subfolders (the CLI's, new in 0.5.1, and the session hook's) happens only inside a
  git repository: `ygg` run in `~` no longer picks up the main tree three folders down, and a session started
  in `~` no longer announces it.
- `ygg log "..." --tag decision --for NOTE` without a run adds `for [[NOTE]]` to the entry instead of failing
  with "--log and --for describe a run" (trial 20).
- Analysis scripts belong in the repository: the `ygg:tree` skill says so (a script whose output feeds a
  result is committed before it is cited, never left in `/tmp`), and the post-Bash hook reminds Claude when
  a command runs or writes a script outside the repository.
- Subagents write confidence at most `medium`: the pre-Bash hook refuses `--confidence high` or `refuted`
  from a subagent's `ygg` command (hooks see its `agent_id`), and the `ygg:tree` skill tells the main
  session to raise confidence itself after review, and to tell subagents it gives tree work to load the skill.

## 0.5.1 (2026-10-22), tree format 2

- Run from a repository whose tree sits in a subfolder (`research/tree`), `ygg` now finds that tree, as the
  hooks already did, instead of failing with "no ygg.json"; with several trees below, it names them and asks
  for `--vault`.

## 0.5.0 (2026-10-22), tree format 2

- Questions for the user: decisions only the user can make (scope, a definition, go or no-go), as notebook
  lines with an id, `- [ ] ask a261022-1 · on [[X]] · blocks [[Y]] · QUESTION`, written with
  `ygg log --ask QUESTION --on NOTE --blocks NOTE`. `ygg asks` lists them; `ygg answer ID -m TEXT` answers
  one in a new entry and ticks its box. Open questions lead `ygg report`, the session briefing and the web
  app's Overview, where each has a box to answer it (the one notebook entry the web app writes); notes they
  are about or block carry a badge, and the **Waiting on you** filter finds them. Answers since the last
  handoff are listed for the next session to act on, and their notes join the agent's list.
- `ygg log` warns when an entry, a handoff above all, leaves a decision to the user in prose ("You: accept or
  reject ...", "your call") instead of asking it with `--ask`.

## 0.4.2 (2026-10-22), tree format 2

- `ygg report` leaves superseded notes out of its work lists (high priority, in progress, open, unanswered
  questions, weak claims) and lists those not done in their own group; the session hook's agenda and the web
  app's "What the agent sees first" leave them out too.
- `ygg log --pid` replaces a wrong PID with the process writing the run's log: one that has exited (`$!`
  after `setsid`, which forks) or is the shell running the command (what `pgrep -f PATTERN` finds first).
  Runs were logged with such PIDs and showed as ended while still running. For a job started with `setsid`
  (`setsid nohup bash -c 'fit; plot'`), it is the session's leader, which runs until every step is done.
- `ygg set --priority` on a done note says that a done note is on no priority list, rather than advising
  a superseding note.

## 0.4.1 (2026-10-22), tree format 2

- `ygg watch` prints the last lines of each log when a run ends (`--tail N`, 5 by default; a progress bar
  shows its final state), so it replaces waiting and then reading the log.
- `ygg log --pid` points to `ygg watch` when it logs a run.
- The session hook says when the tree has uncommitted changes, the sign of a session that stopped before
  recording and committing its work.
- A pre-Bash hook stops wait loops polling `pgrep -f PATTERN`, which never end (the loop's own shell matches
  the pattern), and points to `ygg watch`. The post-Bash hook no longer suggests `pgrep -f` for a run's PID.

## 0.4.0 (2026-10-22), tree format 2

- To-dos: Markdown task lines in notebook entries, written with `ygg log --todo TEXT` and ticked with
  `ygg tick TEXT` (which overwrites the one character in place, the only change ever made to a past entry).
  `ygg report` lists the open ones, and the session hook counts them.
- Issues, for problems in something results rest on (a bug, bad recordings): `ygg log --issue --affects NOTE`
  writes an issue line with an id; `ygg issues` lists the notes resting on what it affects and which are still
  to judge (rerun and superseded, or named with the issue id in a later notebook line); `ygg impact NOTE`
  lists what rests on any note; `ygg resolve ID` closes it. Open issues appear in `ygg report`, `ygg show`, the
  session hook and the web app.
- Web app, transparency first: an **Overview** panel (with nothing selected) shows what the agent is told:
  its list of notes (in progress, high priority, named in the last handoff), open to-dos (tickable), open
  issues, runs needing action, the last handoff, recent entries, and the session briefing word for word.
  It follows the notebook live.
- Web app: priority can be set from the note panel and the Overview; high-priority notes carry a badge.
- Web app: a **Frontier** filter shows only open notes and gaps, cut loose from the done notes above them;
  a **What the agent sees first** filter; superseded notes are hidden by default, the note replacing each
  taking its place (a toggle shows them, faded); notes under an open issue carry a badge.
- DESIGN.md: a Workflows section for a bug in data or code, and the web app's purpose.

### Fixes since 0.3.0

- `ygg log --log PATH` given relative to the repository but run inside the tree's folder finds the log
  at the repository's top, instead of recording a path that does not exist.
- `ygg watch` no longer reports a failure for any `nan` in a log (a QC line printing `freq=nan`), only for
  a NaN loss, gradient or objective, or "NaN detected/encountered".
- `ygg:handoff` carries open to-dos over instead of writing them again (they were listed twice).
- `--vault` is accepted after the command too (`ygg check --vault PATH`).
- Evidence not yet done without a Source is planned work, flagged open, no longer a gap.
- A run logged `--for` a note is no longer flagged (in `ygg report` or listed by `ygg runs`) once something mentions it, though its note is not done
  (a run for a Question stayed flagged for as long as the Question was open).
- The post-Bash hook ignores commands that run `ygg` anywhere, words inside quotes and heredocs, and
  background commands that only wait (a loop on `pgrep` or `sleep`, `tail -f`).
- Seeded notes are matched to their originals by note id alone, so `ygg compress` into a clone of the main
  tree in a folder of another name still maps them back.
- `ygg seed --depth N` brings each Claim's Evidence along; it left them behind, and the copies failed `ygg check`.

## 0.3.0 (2026-10-22), tree format 2

- Notes in no project (no root reaches them) are allowed: `ygg check` warns instead of failing, which is why
  the tree format is now 2 (an older ygg would fail such a tree). `ygg init` upgrades a tree. `ygg report` lists
  them as "In no project", also with `--project`, and the web app shows them with any project selected.
- `out-of-scope: true` (`ygg new/set --out-of-scope`, `--in-scope` to undo) marks a note that belongs in another
  tree; it may be set on done notes. Such notes leave the report's work lists for their own group, get their
  own flag and Show filter in the web app, and `ygg compress` lists them, with the notes in no project, as
  candidates to move out.
- The web app's note panel shows `priority`, `origin` and `out-of-scope`.
- Every tree keeps a notebook, the main tree too ("main" is how a tree is used, not a kind of tree): run
  `ygg init` in an older tree to add it. `ygg:brainstorm` ends a session with a `brainstorm` entry of the ideas
  set aside and the threads left open, and points to `ygg:seed` for a new project.
- The session hook mentions brainstorming, seeding and compression in every tree.

## 0.2.0 (2026-10-22), tree format 1

- `ygg seed NOTE --from MAIN`: copy main-tree notes with everything under them into a project tree, each copy
  recording its `origin` (a new optional field, which older ygg versions ignore, so the format is unchanged).
- `ygg compress` maps seeded notes back onto their originals and, on a second compression of the same tree,
  lists only what changed since the last one.
- `ygg report` is shorter: empty groups are left out and each group lists 8 notes (`--all` for every one).
- Runs: `ygg log TEXT --pid N --log PATH [--job ID] [--for NOTE]` logs a run in the notebook as one
  standard line with a run id and the host. `ygg runs` lists those still running or not looked at,
  `ygg drop` gives runs up (`--kill` stops them), and `ygg watch` waits for runs to end, reporting failures
  and quiet logs as they happen. PIDs and logs are checked on their own host only. The report and the
  session hook give one summary line and flag what needs action: ended runs since the last handoff that
  nothing mentions, ended runs whose `for` note is not done, and running ones whose logs went quiet.
  PIDs are checked through `/proc`, else `ps`, else `kill -0`, catching zombies and reused PIDs, and
  reported "not checkable here" when nothing can tell. Log paths are stored relative to the repository.
- The notebook is appended to in one write in append mode (concurrent writers lose nothing), and `ygg init`
  marks it `merge=union` in `.gitattributes`.
- DESIGN.md has a Workflows section: brainstorming in the main tree, a coding project in its own tree, and
  the life of a run (logged, then evidence, a notebook line, or dropped).
- `ygg --version`; clearer messages for trees in another format.
- Plugin: the `ygg:seed` skill; a PostToolUse hook that reminds Claude to keep the notebook after commits and
  run launches in a repository with a tree; the session hook now finds trees in folders named `tree`.
- Tests in `tests/`.

## 0.1.0 (2026-10-21), tree format 1

The first plugin release: the `ygg` CLI and web app, the skills `tree`, `paper`, `digest`, `brainstorm` and
`handoff`, and the SessionStart hook.
