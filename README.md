# ygg

A research record that an AI agent keeps alongside you while you work, so that weeks of runs, results, dead ends and half-formed ideas stay findable and connected.

## Overview

Computational research produces far more than ends up in a paper: hundreds of runs, small methods decisions, results that were later overturned, questions shared between projects. ygg keeps all of it as a **discourse graph**: one short note per idea, each a **Question**, **Claim**, **Evidence**, **Source** (a paper, a run) or **Dataset**, joined by typed relations (*Evidence supports Claim*, *Claim addresses Question*, ...). Every note carries a work status and an explicit confidence. The notes are plain Markdown in an [Obsidian](https://obsidian.md) vault (a **tree**), compatible with the [Discourse Graph](https://github.com/DiscourseGraphs/discourse-graph) and [TaskNotes](https://github.com/callumalpass/tasknotes-spec) plugins.

The record has three layers, each a cleaned-up version of the one below:

| Layer | Holds | Written |
|---|---|---|
| Lab notebook (`NOTEBOOK.md`) | everything, dated, as it happens | continuously, by you and the agent |
| Project tree (in the project's repository) | settled results, open questions, planned runs | when something settles |
| Main tree (its own repository) | the generalizable results of every project | when a project or phase ends |

Work flows down from the main tree into a project (**seeding**) and back up when it is done (**compression**).

Mostly the agent writes the tree and you steer it. ygg comes in three parts:

- **`ygg`**, a command line tool, and the only thing that writes a tree. It enforces the format: finished notes are frozen, claims need evidence, runs are logged with their processes and logs and are flagged if nobody looks at their results.
- **`ygg serve`**, a local web app that draws the tree and shows what the agent will be told to do next. There you answer its questions, reorder its priorities, tick to-dos and add notes.
- **A [Claude Code](https://claude.com/claude-code) plugin** that teaches Claude to work in a tree. When a session starts in a tree, it is told where the work stands (the last handoff, what is running, what waits on you). Skills cover adding papers (via Zotero), brainstorming, starting a project, handing off at the end of a session, and compressing a project.

### Quick start

You need Python 3.10+, [uv](https://docs.astral.sh/uv/) (for the web app) and, for the agent side, Claude Code.

```bash
claude plugin marketplace add Charles-Fieseler-Vienna/yggdrasil
claude plugin install ygg@yggdrasil

# For your own shell (the plugin puts ygg on Claude's PATH only):
git clone https://github.com/Charles-Fieseler-Vienna/yggdrasil
ln -s "$PWD/yggdrasil/bin/ygg" ~/.local/bin/ygg

ygg init ~/research/main-tree --main   # once: the main tree, where projects start and end up
cd my-project && ygg init research/tree --project "My project"
ygg serve --open        # http://localhost:8765
```

Then start a Claude Code session in the project and work as usual: ask it to brainstorm, add a paper, or hand off when you stop. Open `research/tree` in Obsidian if you want to read or edit the notes there too.

ygg is a personal research tool in active development (see `CHANGELOG.md`). It runs on Linux and macOS. The format is stable enough that trees are upgraded in place (`ygg init`), but expect rough edges.

## For AI agents

Most of what an agent needs is delivered by the plugin, not this file:

- **Session hook** (`hooks/session_start.py`): in a repository with a tree, it gives the rules in brief and where the work stands. Repositories without a tree get nothing.
- **Skills**: `ygg:tree` holds the working rules and should be loaded before changing any tree. The others are task workflows: `ygg:paper`, `ygg:digest`, `ygg:brainstorm`, `ygg:seed`, `ygg:handoff`, `ygg:compress`.
- **Bash hooks**: `hooks/pre_bash.py` and `hooks/post_bash.py` catch common mistakes: `pgrep` wait loops, unlogged runs, result scripts left in `/tmp`, commits with no notebook entry.
- **`DESIGN.md`**: the full specification, covering every field, relation, check and command, and the web app.

If you are working without the plugin, these are the essentials:

1. **A tree is a folder with `ygg.json`.** Nodes are in `tree/`, relations in `relations.json`, project notes in `ideas/`, and the notebook is `NOTEBOOK.md`. `ygg` finds the tree from the working directory, or takes `--vault PATH`.
2. **Write only through `ygg`.** Never edit `tree/`, `relations.json`, `ygg.json`, `templates/` or `.obsidian/` directly. The one exception is the prose of project notes in `ideas/`. The notebook is append-only, through `ygg log`.
3. **Know which tree you are in.** `ygg main` prints the user's main tree; `ygg seed` copies from it and `ygg compress` records into it. If none is set, ask the user which it is before seeding or compressing.
4. **Start with `ygg report`.** Its first list is the work in order, as the user may have set it. Questions waiting on the user come first; do not start notes they block. `ygg show NOTE` reads a note with its relations.
5. **Done notes are frozen.** Supersede one with a new note rather than editing it. Claims need supporting Evidence; Evidence needs `confidence`, an `outcome`, a Conclusion and Caveats. Uncertainty is stated, never implied.
6. **Log runs when they start**, with `ygg log "what and why" --pid N --log PATH`, and wait for them with `ygg watch` instead of a polling loop. A result that matters becomes a run Source (`repository@commit:path`, a real commit) and Evidence derived from it.
7. **Ask, don't decide.** Leave a decision that belongs to the user as `ygg log --ask "..."`, not as prose in a handoff.
8. **Run `ygg check`** after each batch of changes. It exits 1 on any error.

`ygg --help` and `ygg COMMAND --help` list the commands.

### Working on ygg itself

Read `DEVELOPING.md` first: layout, tests, versions, and how the web app is built. Test only on scratch trees (`ygg init` one in a temporary folder), never on a real one. Add a test with every change to the CLI or hooks, and keep `DESIGN.md` in step with any change in behaviour. Run the tests with:

```bash
uv run --no-project --with pytest pytest tests
```

Known small issues are in `TODO.md`.

## License

MIT
