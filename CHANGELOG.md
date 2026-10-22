# Changelog

ygg has two versions. The **tool version** (`ygg --version`, `.claude-plugin/plugin.json`) follows
semantic versioning for the CLI, web app, skills and hooks. The **tree format** (`spec_version` in each
tree's `ygg.json`) changes only when a tree written by a new ygg could fail the checks of an older one;
`ygg init` upgrades a tree to the current format, and every command warns about a tree in another format.

## Unreleased

- `--vault` is accepted after the command too (`ygg check --vault PATH`).
- Evidence not yet done without a Source is planned work, flagged open, no longer a gap.
- A run logged `--for` a note is no longer flagged (in `ygg report` or listed by `ygg runs`) once something mentions it, though its note is not done
  (a run for a Question stayed flagged for as long as the Question was open).
- The post-Bash hook ignores commands that run `ygg` anywhere, words inside quotes and heredocs, and
  background commands that only wait (a loop on `pgrep` or `sleep`, `tail -f`).
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
