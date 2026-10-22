# Changelog

ygg has two versions. The **tool version** (`ygg --version`, `.claude-plugin/plugin.json`) follows
semantic versioning for the CLI, web app, skills and hooks. The **tree format** (`spec_version` in each
tree's `ygg.json`) changes only when a tree written by a new ygg could fail the checks of an older one;
`ygg init` upgrades a tree to the current format, and every command warns about a tree in another format.

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
