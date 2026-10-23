# Developing ygg

How to work on ygg itself: the CLI, the hooks, the skills and the web app. What ygg does, and the format it
writes, is specified in `DESIGN.md`; keep that in step with any change in behaviour. This document is about
the code and the working loop, not about using a tree.

## Layout

```text
yggdrasil/
├── .claude-plugin/   # plugin.json (the plugin, with its version) and marketplace.json
├── bin/ygg           # the plugin's `ygg` command on Claude's PATH; uses uv only for `serve`
├── hooks/            # SessionStart, pre-Bash and post-Bash hooks (hooks.json wires them)
├── skills/<name>/SKILL.md   # tree, seed, paper, digest, brainstorm, handoff, compress
├── scripts/
│   ├── ygg           # the CLI, one file
│   ├── ygg_server.py # the web app's server
│   └── web/          # the web app's page
├── schema/           # the schema as a DG export (`ygg schema`)
├── tests/            # pytest: the CLI, the hooks, the web app (opt-in)
├── DESIGN.md         # the specification
├── DEVELOPING.md     # this file
├── CHANGELOG.md
└── TODO.md           # known small issues, waiting
```

The plugin is installed from this folder through the local `yggdrasil` marketplace and read in place, so
changes to skills, hooks and the CLI apply in the next session started anywhere.

## Ground rules

- **Test on scratch trees, never on a real one.** The user's main tree is `~/Current_work/repos/Yggdrasil-charlie`;
  project trees live in their projects (e.g. `Cosyne_2027/research/tree`). Clone one into a scratch folder
  (`git clone ~/Current_work/repos/Yggdrasil-charlie $S/tree`) and run `bin/ygg --vault $S/tree ...`, or
  `ygg init` a fresh one. Scratch clones are yours to break; the rule that trees change only through `ygg`
  holds for real ones.
- **Processes**: kill only those you started. `ygg serve` never returns; the user may have their own on 8765.
- In skills, write `ygg`, never `scripts/ygg`, and `${CLAUDE_PLUGIN_ROOT}/DESIGN.md` for the spec.

## Tests and checks

```bash
uv run --no-project --with pytest pytest tests          # the CLI and hooks, against throwaway trees (~1 min)
YGG_WEB_TESTS=1 uv run --no-project --with pytest --with playwright pytest tests/test_web.py   # Chrome
claude plugin validate .                                 # after changing the plugin (the CLAUDE.md warning is expected)
python3 scripts/ygg --vault ~/Current_work/repos/Yggdrasil-charlie check   # before committing a change that could affect trees
```

- Add a test with every change to the CLI or hooks. `tests/conftest.py` has the fixtures: `tree` (a fresh
  tree in a git repository), `populated` (question, evidence, claim, all done and committed), `project` (a
  project repository for seed and compress), and `run`/`ygg` to call the CLI as users do, on plain `python3`.
- Freezing is judged against `HEAD`, so a test about it must `commit()` the state it starts from; a test
  that strips fields from a note committed with them tests something else (and may pass by timing).
- Check a new test fails without the change it covers.

## Versions

- The tool version: `__version__` in `scripts/ygg` and `version` in `.claude-plugin/plugin.json`, bumped
  together with a `CHANGELOG.md` entry (a test checks they agree). Bump it when the skills, hooks or CLI
  change in a way users should pick up.
- The tree format: `SPEC_VERSION`, bumped only when trees written by the new ygg could fail an older one's
  checks; `ygg init` must then upgrade older trees. Prefer a clearer error over a format change (e.g. a
  `run` given as `owner/repo@...` is refused with the bare form, rather than accepted).

## The CLI

`scripts/ygg` is one file, a uv script whose header declares the web app's dependencies; every command but
`serve` is standard library only and runs on plain `python3`. The parts most changes touch:

- `Vault` reads a tree: notes (`Note`, with frontmatter kept in order and only changed keys rewritten),
  `relations.json`, projects, and `membership()`, from which `sync()` writes `projects:`.
- `note_errors` (one note) and `all_errors` (the tree, including `frozen_errors` against `HEAD`) are what
  `check` runs; commands call `check_note` before writing, so a refused command writes nothing.
- The notebook: `notebook_entries`, `all_todos`, `issue_states`, `all_asks`, `run_states` and `needs_action`.
- `agenda` is what a session is pointed at first. The session hook, `ygg report` and the web app's Overview
  all build on these same functions, so what the user sees is what the agent is told. Keep it that way: a
  new kind of thing the agent is told belongs in all three.
- Error and warning text is read by agents more than by people. Say what was wrong and the command that
  fixes it; trials show a vague refusal costs a retry or two each time.

## Hooks

Each hook is a small script reading the event JSON on stdin and printing nothing where no tree is found.
`session_start.py` loads `scripts/ygg` as a module (`SourceFileLoader`) and calls its functions, so the
briefing never drifts from the CLI. The hook input carries `cwd`, and for a subagent's tool call `agent_id`
and `agent_type`, but not the model; the subagent confidence cap in `pre_bash.py` therefore applies to all
subagents. Test hooks through `tests/test_hooks.py` (`hook(name, event)`, `guard(cwd, command, **event)`).

## The web app

The behaviour is specified in `DESIGN.md` (Web app). The implementation:

- **Server**: `scripts/ygg_server.py`, FastAPI under uvicorn, started by `ygg serve`, which passes the CLI
  module in (`ygg_server.serve(sys.modules[__name__], ...)`). It rebuilds the graph from the files on every
  read and keeps no cache. `graph_json` and `overview_json` build the two main payloads from the CLI's own
  functions. Every write runs the CLI in a subprocess (`Tree.run`), one at a time, so it passes the same
  checks; a refusal becomes a 400 carrying the command's error. `watchfiles` watches `tree/`, `ideas/`,
  `relations.json` and `NOTEBOOK.md`, and `/api/events` (server-sent events) pushes a new version to the page.
- **Security**: it listens on 127.0.0.1, refuses a `Host` other than `localhost` or `127.0.0.1`, and
  requires a per-run token embedded in the served page on every API call (the `X-Ygg-Token` header, or `?t=`
  for the event stream, which cannot send headers).
- **Page**: `scripts/web/`, React and React Flow with no build step. An import map in `index.html` loads
  pinned modules from esm.sh (so it needs the network; vendoring them is in `TODO.md`), and the code uses
  `htm` instead of JSX. The modules: `graph.js` (what is shown: folding, filters, frontier; pure functions),
  `layout.js` (positions), `animate.js` (moving between layouts), `api.js`, `note.js` (the card),
  `edges.js` (the relation curves), `toolbar.js`, `panel.js` (side panel and Overview), `dialogs.js` and
  `main.js` (state, kept per vault in the browser).

### Working on it

1. Make a scratch tree worth looking at: a clone of the main tree, or a copy of a real project tree
   committed in a scratch repository (the Cosyne tree, ~85 notes; the BarlowTrack tree, ~95):
   ```bash
   mkdir -p $S/web && cp -r ~/Current_work/repos/barlow_track/research/tree $S/web/
   cd $S/web && git init -q && git add -A && git -c user.name=t -c user.email=t@t commit -qm scratch
   ```
2. Serve it in the background on a spare port and keep the PID:
   `bin/ygg --vault $S/web/tree serve --port 8791 &`. Open `http://localhost:8791/`.
3. Edit the files in `scripts/web/` and reload the page; there is nothing to build. Changes to
   `ygg_server.py` or `scripts/ygg` need the server restarted.
4. Look at it, not only at the code. A Playwright script can take screenshots
   (`uv run --no-project --with playwright python shot.py`, `chromium.launch(channel="chrome")`). Wait for
   the `load` state, not `networkidle`: the event stream keeps the network busy forever. Collect `pageerror`
   and console errors as `tests/test_web.py` does.
5. To call the API by hand, take the token from the served page; without it every call is a 403.
6. Add to `tests/test_web.py` for a new interaction, run it, and stop your server.

## Trial rounds

The skills and hooks are tested by headless sessions doing real work in a project tree, then reading what
went wrong. A round, on a branch of a project repository made for it (e.g. `ygg-trial` in Cosyne_2027):

```bash
claude -p "Continuing the <project> work on the <branch> branch. Catch up, then work through the next steps
in order of priority for about 30 minutes of work. I'm away and can't answer questions: make the judgment
calls yourself and record your reasoning. When done, hand off, and commit to <branch> (don't push)." \
  --model sonnet --permission-mode auto --max-budget-usd 15 --output-format stream-json --verbose > trial.jsonl
```

- Use Sonnet (and sometimes Haiku, as main session or subagents): they are the models that will use ygg day
  to day, and cheaper. Run one round at a time per repository, since rounds commit.
- Review the transcript for every `ygg` error and warning, hook denial, retry, and wrong belief the agent
  states about ygg (in its summary and handoff too). Then `ygg check`, `ygg runs` and `git log` in the tree.
- A round is clean when it hits no ygg bug. Fix what it finds (a clearer message, a skill line, a check),
  with a test, and run another; aim for several clean rounds in a row. Soft suggestions to the user in prose
  are fine; decisions left to the user in prose are not.
- Skills and other trial targets (paper, digest, seed, compress, brainstorm) can run on scratch copies.
  Rounds must not write to the user's Zotero library.
