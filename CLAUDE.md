# CLAUDE.md

This repo is **ygg**, the tool for the user's discourse-graph research trees: the CLI, its web app, and the Claude Code plugin that teaches Claude to work in a tree. It holds no tree itself. The user's main tree is the sister repository `~/Current_work/repos/Yggdrasil-charlie`; project trees live in their projects (e.g. `Cosyne_2027/research/tree/`).

- `DESIGN.md` specifies what ygg does: the format, the commands, the web app's behaviour, the plugin. Keep it in step with any change in behaviour.
- `DEVELOPING.md` is how to work on it: layout, tests and checks, versions, the code of the CLI, hooks and web app, the web app's working loop, and trial rounds. Read it before changing anything.
- `TODO.md` holds known small issues; `CHANGELOG.md` the versions.

Rules that hold in every session here:

- Test on scratch trees, never on a real one. When working inside a real tree anyway (the user's request), follow the `ygg:tree` skill.
- Kill only processes you started; the user may have their own `ygg serve` open on 8765.
- Add a test with every change to the CLI or hooks, and bump the version with a `CHANGELOG.md` entry when users should pick a change up.

Commit only when the user asks.
