# CLAUDE.md

This repo is **ygg**, the tool for the user's discourse-graph research trees: the CLI, its web app, and the Claude Code plugin that teaches Claude to work in a tree. It holds no tree itself. The user's main tree is the sister repository `~/Current_work/repos/Yggdrasil-charlie`; project trees live in their projects (e.g. `Cosyne_2027/research/tree/`). `DESIGN.md` is the full specification; keep it in step with any change to the format, the commands, the web app or the plugin.

## Layout

- `scripts/ygg`: the CLI, one file. A uv script; every command but `serve` is standard library only and runs on plain `python3`.
- `scripts/ygg_server.py` and `scripts/web/`: the web app (FastAPI, and React Flow with no build step).
- `bin/ygg`: the plugin's `ygg` command; uses uv only for `serve`.
- `skills/<name>/SKILL.md`: the plugin's skills, `ygg:tree` (the working rules), `ygg:seed`, `ygg:paper`, `ygg:digest`, `ygg:brainstorm`, `ygg:handoff`. Write `ygg`, never `scripts/ygg`, in them, and `${CLAUDE_PLUGIN_ROOT}/DESIGN.md` for the spec.
- `hooks/`: the SessionStart hook (the rules and the tree's state) and the post-Bash hook (notebook reminders), both silent where no tree is found.
- `.claude-plugin/`: `plugin.json` and `marketplace.json`. Bump the plugin `version` when the skills or hooks change in a way users should pick up.

## Working on it

- **Test on scratch trees, never on a real one.** Clone `Yggdrasil-charlie` into your scratchpad (`git clone ~/Current_work/repos/Yggdrasil-charlie $S/tree`) and run `bin/ygg --vault $S/tree ...`, or `ygg init` a fresh one. The rule that trees change only through `ygg` holds for real trees; scratch clones are yours to break.
- When working inside a real tree anyway (the user's request), follow the `ygg:tree` skill.
- `ygg serve` never returns: run it in the background on a spare port against a scratch tree, keep its PID, and kill only processes you started; the user may have their own server open on 8765.
- Tests: `uv run --no-project --with pytest pytest tests` (the CLI and hooks, against throwaway trees, in seconds). The web app's browser test is opt-in: `YGG_WEB_TESTS=1 uv run --no-project --with pytest --with playwright pytest tests/test_web.py` (Chrome). Add a test with every change to the CLI or hooks.
- Versions: bump `__version__` in `scripts/ygg` and `.claude-plugin/plugin.json` together, with a `CHANGELOG.md` entry (a test checks they agree). Bump `SPEC_VERSION` only when trees written by the new ygg could fail an older one's checks, and make `ygg init` upgrade older trees.
- Known small issues wait in `TODO.md`.
- After changing the plugin: `claude plugin validate .` (its warning about this `CLAUDE.md` at the plugin root is expected). The plugin is installed from this folder through the local `yggdrasil` marketplace, so changes apply in new sessions.
- Run `python3 scripts/ygg --vault ~/Current_work/repos/Yggdrasil-charlie check` before committing a change that could affect existing trees; a spec change needs `ygg init` to upgrade them.

Commit only when the user asks.
