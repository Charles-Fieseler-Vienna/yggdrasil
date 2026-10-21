# Research Notes Design

> **Status: draft (2026-10-21).** This version moves the format onto the Discourse Graph (DG) Obsidian plugin and TaskNotes frontmatter, managed with `ygg`, which ships as a Claude Code plugin.

## Problem

I have a ton of computational experiments and ideas, and they are interrelated and hard to keep track of. Multiple projects share semi-organized nodes (`research/FRAMEWORK.md`, `research/SSL_ALIGNMENT.md`, fly/mouse decomposition, the data repository, `barlow_track`). Maintaining one file per project would duplicate shared nodes and require project interfaces to be updated manually.

The record has to work for ongoing work, not only for finished results: what is being run now, what is blocked, and what is still a guess.

## Protocol

- Every durable tree note is a Question, Claim, Evidence, Source or Dataset.
- Every note has one main idea.
- Relations are typed.
- Uncertainty is explicit.
- Investigations and run groups are represented by Source or Evidence notes rather than requiring individual run nodes.
- Custom node types are allowed when the core four are insufficient. Dataset is the one custom type so far.

## Design

A **tree** is an Obsidian vault of plain Markdown, maintained mainly by Claude through `ygg`. The **main tree** (`Yggdrasil-charlie`, a separate private repository) holds only **compressed** nodes: the generalizable questions, claims, evidence and dead ends of each project. Each project keeps its detailed tree in its own repository, in the same format (see [Trees in projects](#trees-in-projects)). This repository, `yggdrasil`, holds no tree: it is the tool, the web app and the Claude Code plugin that teaches Claude the format (see [Plugin](#plugin)). Three standards define the format, and ygg adds only what they lack:

| Layer | Standard | Owns |
|---|---|---|
| Discourse graph | [Discourse Graph Obsidian plugin](https://github.com/DiscourseGraphs/discourse-graph) (`apps/obsidian`) | node types (`nodeTypeId`, `nodeInstanceId`), typed relations (`relations.json`) |
| Work status | [TaskNotes spec](https://github.com/callumalpass/tasknotes-spec) 0.2.0 | `status`, `priority`, `scheduled`, dates, `projects` |
| Research record | this document | `confidence`, `outcome`, evidence references, freezing, project membership, `check` |

A tree is **text only**. Figures, data and code live in project repositories or on the cluster and are referenced, never copied in.

A tree (the main tree, or `research/tree/` in a project):

```text
Yggdrasil-charlie/
├── tree/             # every graph node: Question, Claim, Evidence, Source, Dataset
├── ideas/            # project and paper notes: light frontmatter, free prose
├── templates/        # one DG node template per type (written by `ygg init`)
├── relations.json    # every relation; written by the DG plugin or ygg
├── ygg.json          # marks the folder as a ygg tree, with its spec version
├── NOTEBOOK.md       # the lab notebook (project trees; see Notebook)
└── .obsidian/plugins/{discourse-graphs,tasknotes}/data.json   # plugin settings (written by `ygg init`)
```

The tool:

```text
yggdrasil/
├── .claude-plugin/   # plugin.json and marketplace.json (see Plugin)
├── bin/ygg           # the command, put on Claude's PATH by the plugin
├── hooks/            # the SessionStart hook
├── skills/           # tree, paper, digest, brainstorm, handoff
├── schema/
│   └── dg-schema-yggdrasil.json   # the schema as a DG export, for manual import (`ygg schema`)
├── scripts/
│   ├── ygg           # the CLI
│   ├── ygg_server.py # the web app's server
│   └── web/          # the web app's page
├── CLAUDE.md         # how to develop the tool
└── DESIGN.md
```

## Node types

All nodes live in `tree/`. `ideas/` holds only the higher-level project and paper notes, which are not graph nodes.

| Type | Title format | What it is |
|---|---|---|
| Question | `QUE - …` | An open question or hypothesis: "Is the head wave driven at the head?" |
| Claim | `CLM - …` | An assertion supported by evidence. Includes claims about methods ("non-contrastive losses are sufficient for SSL alignment here"); there is no separate decision type. |
| Evidence | `EVD - …` | What one run, run group or investigation showed: purpose, method, results, conclusion, caveats. |
| Source | `@…` | A paper (`zotero`, `doi`; see [Papers](#papers)), a run or run group with an immutable reference (`run`), or a detailed project tree. |
| Dataset | `DATA - …` | A dataset, or one version or subset of it, that results are established on. |

The filename is the title (DG's format and TaskNotes' default `title.storage: filename`). A title states one idea: no semicolons, no sub-claims, no guesses at causes, no figure references. Details, qualifications and figure panels go in the body. Source keeps DG's default format, `@{content}`. Identity is `nodeInstanceId`, so renaming a note does not break its relations.

**Questions and Claims stay separate.** A question is not turned into a claim as evidence accumulates; a Claim that `addresses` it is created instead. Small, near-duplicate Questions and Claims are expected while a project is ongoing and are cleaned up when the project is compressed (see [Compression](#compression)). A note never changes type.

**Datasets are their own type** because every claim holds only with respect to the data it was established on. Each version or subset (exploration subset, full cohort) is its own Dataset node, `derived from` its parent. A claim's scope is derived, not stored: `ygg show` follows Claim ← supports ← Evidence → derived from → Source → derived from → Dataset and reports the datasets it rests on.

The node types, relation types, allowed pairs and templates are defined in `scripts/ygg`. `ygg init` writes them into the DG plugin's settings (`.obsidian/plugins/discourse-graphs/data.json`) with fixed ids such as `node_ygg_claim` and `relation_ygg_supports`, so every tree uses the same ids and no import step is needed. `schema/dg-schema-yggdrasil.json` is the same schema as a DG export file, for importing by hand.

## Relations

Relations are stored only in `relations.json` at the vault root, the DG plugin's format: one record per relation with the source and destination `nodeInstanceId` and the relation type id. Notes do not contain links of their own. Inline `[[links]]` in prose are allowed but carry no relation type.

| Relation | From → to | Complement |
|---|---|---|
| `informs` | Evidence → Question | is informed by |
| `supports` | Evidence → Claim | is supported by |
| `opposes` | Evidence → Claim | is opposed by |
| `derived from` | Evidence → Source, Dataset; Source → Source, Dataset; Dataset → Dataset | has derivation |
| `addresses` | Claim → Question | is addressed by |
| `follows from` | Question → Question, Claim; Claim → Claim | leads to |
| `supersedes` | same type → same type (any type) | is superseded by |
| `blocked by` | Question, Claim, Evidence → Question, Claim, Evidence | blocks |

- `informs` is for evidence that bears on a question without settling a claim. Evidence that settles something `supports` or `opposes` a Claim.
- `follows from` records that a question or claim came out of an earlier one. It is how follow-up questions join their parent's project.
- `blocked by` is work ordering only, never an epistemic relation. It replaces TaskNotes' `blockedBy` frontmatter field, which is not used.
- Adding a relation never edits a note, so relations may be added to `done` notes at any time (a later Claim supported by finished Evidence, for example). Relations touching a `done` note cannot be removed.
- Relations carry no annotation; explain a non-obvious relation in the body of the newer note.

## Frontmatter

Every node carries DG's identity fields and TaskNotes' task fields. The TaskNotes spec requires unknown fields to be preserved, so the two plugins coexist.

```yaml
---
nodeTypeId: node_ygg_evidence           # DG: node type (vault-local id after import)
nodeInstanceId: 0192f3a1-…              # DG: stable identity, uuidv7
status: done                            # open | in-progress | done
priority: normal                        # none | low | normal | high
scheduled: 2026-10-10
dateCreated: 2026-10-10T14:02:00+02:00
dateModified: 2026-10-11T09:12:00+02:00
completedDate: 2026-10-11               # required by TaskNotes when status is done
projects:                               # GENERATED by ygg; never edit
  - "[[control-decomposition]]"
confidence: medium                      # Claim, Evidence
outcome: succeeded                      # Evidence
---
```

| Field | On | Notes |
|---|---|---|
| `nodeTypeId`, `nodeInstanceId` | all | DG; never change |
| `title`, `status`, `priority`, `dateCreated`, `dateModified` | all | TaskNotes; `status` and dates required |
| `scheduled`, `completedDate` | all | TaskNotes; `completedDate` once `done` |
| `projects` | all | TaskNotes field, generated (see [Projects](#projects)) |
| `confidence` | Claim, Evidence | `low`, `medium`, `high`, or `refuted` (Claim only) |
| `outcome` | Evidence | `succeeded`, `failed`, `ambiguous`, `promising-out-of-scope`; required once `done` |
| `run`, `run_start`, `run_end`, `data`, `figures` | Source | the run or run group |
| `tree` | Source | `repository@commit:path` of a detailed project tree (written by `ygg compress`) |
| `zotero`, `doi` | Source | a paper's Zotero item key (8 capital letters or digits) and DOI; at most one Source per paper |
| `citekey` | Source | Better BibTeX citekey, for citing the paper in writing |
| `location`, `n_animals`, `n_recordings` | Dataset | |
| `legacy_ref` | all | where a backfilled note came from, e.g. `"TREE 1.12"` |

TaskNotes should be set to identify tasks by property (`taskIdentificationMethod: property`, `taskPropertyName: nodeTypeId`, empty value), so every node is a task and project notes are not, without a `#task` tag. The pipeline-specific fields of `obsidian_kanban_ai` (`harness`, `agent`, `skills`, `model`, `cli_args`) and its extra statuses are not used.

### Status and freezing

`status` is the work state: `open` (proposed, not started), `in-progress` (being run or worked on), `done`.

A note is editable while it is `open` or `in-progress`, and frozen once it is `done`, whatever its type. A `done` note is never rewritten; a new note of the same type `supersedes` it.

### Uncertainty

`confidence` is required on Claims and Evidence and means:

| Value | Evidence | Claim |
|---|---|---|
| `low` | suggestive; missing controls, small n, or the exploration subset only | plausible from the evidence so far |
| `medium` | holds in the analysed data, with caveats that could change it | supported by evidence without serious opposition |
| `high` | robust across checks and the full cohort | supported by several independent pieces of evidence |
| `refuted` | — | opposed by the evidence |

Every Evidence note has a `## Caveats` section stating missing runs, data limitations and anything else that bounds the result, even if it is "none known". Every Claim is supported by at least one Evidence note; a claim no evidence supports yet stays a Question.

## Bodies

Templates (in the schema file) give each type its sections:

| Type | Sections | Required before `done` |
|---|---|---|
| Question | Question, Context | Question |
| Claim | Claim, Rationale, Scope | Claim |
| Evidence | Purpose, Method, Results, Conclusion, Caveats | Conclusion, Caveats |
| Source | Description | — |
| Dataset | Description, Provenance | — |

The Conclusion of an Evidence note is one to three sentences, readable on their own: what the result means, with effect size, n (animals, recordings) and which Dataset. Failed and ambiguous results are recorded too, with what would make them worth retrying.

## Projects

A project (or paper) note in `ideas/` has light frontmatter and lists its **root** nodes. It is not a DG node or a TaskNotes task.

```yaml
---
type: project
title: "Control decomposition"
created: 2026-10-12
roots:
  - "[[QUE - Is the head wave driven at the head]]"
  - "[[CLM - Body waves are proprioceptively coupled]]"
---

## Summary
## Findings
```

Project membership is stored only in `roots`. Everything else belongs to a project through the graph, walking **down** from the roots:

1. a root is a member;
2. a Question or Claim that `follows from` or `addresses` a member is a member;
3. Evidence that `informs`, `supports` or `opposes` a member is a member;
4. a Source or Dataset that a member is `derived from` is a member, recursively;
5. a note that `supersedes` a member is a member.

The walk never goes back up from a member Evidence note to other Claims it supports, so sharing evidence does not merge projects. Notes reached from two projects are the interface between them.

`ygg` writes the result into each node's `projects:` field so TaskNotes boards can group by project. The field is a cache: `check` fails if it differs from the computed membership.

`## Findings` summarises the project's current conclusions in prose, citing Claims, e.g. `- The head wave is driven at the head ([[CLM - Head wave is driven at the head]]).` It may be revised freely.

## Compression

The main tree holds only compressed nodes. Each project keeps its own detailed tree in its own repository: every step of the logical progression, every small methods question, every diagnostic. `Cosyne_2027@1dffa02:research/TREE.md` is the reference example, with about 50 nodes over ten days. Most of it is not useful to other projects.

When a project, or a phase of one, is finished, its detailed tree is **compressed** into a few generalizable nodes. The test for keeping something is whether it is a generalizable conclusion, rather than a narrowly scoped or very specific methods question, claim or result. Compression is a judgement made with the user, not an automatic step.

- As a guide to size, each figure gets at least one Question, and each Claim is about what one to three of its panels demonstrate. Each Claim has its own Evidence note. A 12-panel abstract yields up to about 12 Claims.
- A compressed Evidence note typically summarises an investigation that spanned many runs.
- Compressed Evidence is `derived from` a Source pointing to the detailed tree at a fixed commit, so a new project that needs a detailed method can walk down into it, and from the Dataset it rests on.
- The project's `roots` list the compressed root nodes.
- Papers are not copied twice. `ygg compress` lists each paper Source of the project tree with the main tree's Source for the same paper (by Zotero key or DOI), if any; compressed Evidence derives from that one. A paper with neither is flagged, to be looked up in Zotero first.

## Papers

Zotero is the one home of the literature. A paper is a Source titled with the paper's title, whose frontmatter holds its Zotero item key (`zotero`, e.g. `2Q9B3YAH`) and, where it has one, its DOI (`doi`, bare, e.g. `10.48550/arXiv.2410.14673`). Its body is at most a line on what the paper is: the bibliographic details, abstract and reading notes stay in Zotero. The web app links each paper to Zotero (`zotero://select/library/items/KEY`) and to its DOI.

What a paper means for a project goes in Evidence derived from it ("Contrastive learning recovers latent dynamics under a nonlinear observation model"), which then informs questions or supports claims. The Source stays a pointer that any project can share, and the Evidence can be weak, strong or superseded like any other.

Within one tree, a paper has one Source: `ygg new` refuses a second Source with the same Zotero key or DOI (compared without case or a `https://doi.org/` prefix), and `check` reports any that slip through, unless one supersedes the other. `zotero:KEY` and `doi:DOI` work wherever a note is named, e.g. `--link derived-from:zotero:2Q9B3YAH`. Separate project trees each make their own Sources; the duplicates are resolved on compression (see [Compression](#compression)).

A paper Source is usually created `--status done`, since there is no work left on it.

## Evidence references

`run` uses an immutable reference, `repository@commit:path`, never a branch. The referenced script should be a single self-contained bash script that contains (or points to, via committed paths) all config and parameters needed to rerun it. `figures` use the same form or an absolute cluster path.

Data lives on the shared cluster and is not version-controlled. To keep it as stable as practical:

- The run script writes a `MANIFEST.txt` into its output directory: commit hash, command, and each output file with size and modification time.
- After a run, the output directory is made read-only (`chmod -R a-w`).
- Lost or moved results are recorded in `data`, e.g. `LOST 2026-10-14: results/highres_innovation/`.

## Trees in projects

A project keeps its detailed tree in its own repository, e.g. `Cosyne_2027/research/tree/`, made with `ygg init` and opened as its own Obsidian vault. It uses the same types, relations, frontmatter and checks as the main tree, at full granularity: every small run, diagnostic and methods question. That is where day-to-day work is tracked (`status`, TaskNotes boards).

When a project or phase is finished, `ygg compress PATH` (run in the main tree) prints the project tree's outline and records it there as a Source at its current commit. The compressed nodes are then written by hand with the user (see [Compression](#compression)).

## Notebook

A project tree has a lab notebook, `NOTEBOOK.md` at its root (made by `ygg init`). It is the raw record under the tree: what was tried, decided, abandoned or guessed, as it happens, before it is settled enough to be a node. Three layers, each a cleaned-up version of the one below:

| Layer | Where | Holds | Written |
|---|---|---|---|
| Notebook | project repository | everything, dated, unedited | as the work happens, by the user and by Claude |
| Project tree | project repository | the graph of settled results, open questions and runs | when something settles |
| Main tree | Yggdrasil-charlie | the compressed, generalizable part | at the end of a phase |

Each entry is a `## YYYY-MM-DD HH:MM` heading, optionally `— tag` (`decision`, `dead-end`, `run`, `idea`, `handoff`), and free Markdown that links nodes as `[[...]]`. Entries are appended, newest last, and never edited or reordered; a correction is a new entry. `ygg log` appends one; `ygg check` warns, without failing, about links to notes that do not exist. ygg never rewrites the notebook.

There is no separate decision log. A decision is first an entry; once it holds, it becomes a Claim (about a method, if it is one) with its Evidence, which may cite the entry's date.

A **handoff** is an entry tagged `handoff`: where things stand, what is running (job IDs, output paths), the next steps as links to nodes, and loose state only the session knows (uncommitted code, scratch paths). Before writing one, the notebook since the last handoff is distilled into the tree: runs, results, decisions and dead ends become nodes, and the next one to three notes get `priority: high`. To catch up, `ygg report --since handoff` lists the high-priority and in-progress notes, the notes changed and the notebook entries since the last handoff. The `ygg:handoff` skill does both. The main tree, being compressed, mostly does without a notebook.

## Tooling

`scripts/ygg` is the only writer of notes and `relations.json` besides the Obsidian plugins' own UIs. It finds its tree by looking for `ygg.json` from the current directory up, or takes `--vault PATH`. The Claude Code plugin puts it on Claude's PATH as `ygg` (`bin/ygg`); for your own shell, `ln -s "$PWD/bin/ygg" ~/.local/bin/ygg`.

It is a [uv](https://docs.astral.sh/uv/) script: its first lines declare Python 3.10+ and the web app's dependencies (FastAPI, uvicorn, watchfiles), and running it directly lets uv provide them. Every command but `serve` is standard library only, so `python3 scripts/ygg ...` also works where uv is missing. `bin/ygg` uses uv only for `serve` and runs everything else on `python3`.

| Command | Does |
|---|---|
| `ygg init [PATH] [--project TITLE]` | Makes PATH a tree: folders, `ygg.json`, `relations.json`, templates, plugin settings. Safe to rerun; it upgrades settings in place. |
| `ygg new TYPE TITLE [--link REL:NOTE] [--link-from REL:NOTE] [--body FILE] ...` | Creates a node (`TYPE` is a node type) or a project note (`project`, with `--root`). |
| `ygg link SOURCE REL TARGET` / `ygg unlink ...` | Adds or removes a relation. |
| `ygg set NOTE [...]` | Changes fields or the body of an editable node, or a project's roots. |
| `ygg done NOTE [--outcome X]` | Finishes and freezes a node. |
| `ygg show NOTE` | Prints a note with its relations (and a claim's datasets), or a project with its members. |
| `ygg report [--project P] [--since DATE\|handoff]` | Lists high-priority and in-progress work, open nodes, unanswered questions, low-confidence claims and orphans; with `--since`, also the notes changed and the notebook entries since then. |
| `ygg log [TEXT] [--tag WORD] [--handoff] [--body FILE]` | Appends a dated entry to the notebook (see [Notebook](#notebook)). |
| `ygg sync` | Regenerates `projects:` and fills in TaskNotes dates missing from notes made in Obsidian. |
| `ygg compress PATH [--dry-run]` | Outlines a project tree and records it as a Source at its commit; refuses uncommitted trees. |
| `ygg serve [--port N] [--open]` | Serves a local web app for browsing and editing the tree (see [Web app](#web-app)). |
| `ygg check` | Validates everything; exits 1 on any error. |
| `ygg schema [--out FILE]` | Prints the schema as a DG export file. |

Notes are named by filename, by the content after the type prefix, by `nodeInstanceId`, or by any unique part of the filename.

`check` enforces:

- frontmatter fields and values as above, TaskNotes' required fields, and `completedDate` on `done` notes;
- filenames carry their type's prefix, and `title`, if present, equals the filename;
- every relation in `relations.json` connects existing nodes with an allowed type pair, with no duplicates;
- `derived from`, `follows from` and `supersedes` contain no cycles;
- `done` Evidence has an `outcome` and non-empty Conclusion and Caveats; `done` Questions and Claims have their main section;
- every Claim is supported by at least one Evidence note;
- every node is reachable from some project's roots, and `projects:` matches the computed membership;
- `done` notes are unchanged since `HEAD` (bar `projects:` and `dateModified`), and relations touching them were not removed;
- `run`, `tree` and `figures` are immutable references; only `.md` files are in `tree/` and `ideas/`;
- the DG settings hold the ygg types and no sync password, and `ygg.json` matches the tool's spec version.

### Web app

`ygg serve` serves a web app at `http://localhost:8765/` (`--port`, `--open` to open the browser) until Ctrl-C.

- The server is a FastAPI app in `scripts/ygg_server.py`, run by uvicorn. It rebuilds the graph from the files on every read, keeping no cache.
- The page is in `scripts/web/`: React with [React Flow](https://reactflow.dev) for the graph. Each module is small: `graph.js` (what is shown; pure functions), `layout.js` (positions), `animate.js` (moving between layouts), `api.js`, `note.js` (the card), `edges.js` (the relation curves), `toolbar.js`, `panel.js`, `dialogs.js` and `main.js` (state). There is no build step. The libraries load from esm.sh at pinned versions through an import map, and `htm` stands in for JSX.

The tree is drawn left to right parent → child: questions lead to their follow-ups, claims and informing evidence, claims to their evidence, evidence to its sources and datasets. Arrowheads mark each relation's real destination. Node colour is the type; the border marks gaps (red), open or in-progress notes (dashed blue) and weak ones (double yellow).

Folding is per node. Ctrl-click (Cmd-click on a Mac) a node to fold or unfold what is under it; a node is shown if it is a root or under an unfolded shown node, so a node shared by several parents appears as soon as any of them is unfolded. A folded node shows how many notes and gaps it hides; hidden gaps also tint it red. By default only the top questions are unfolded.

The layout is a tidy tree, one column per level, with each node's children in a fixed order (by filename, so claims, then evidence, then follow-up questions). It is redone on every change, so unfolding a node only pushes what is below it down, and nothing is reordered. A node with several shown parents sits under the shallowest one, and keeps that place while it stays shown, so unfolding another of its parents does not move it; its other edges are still drawn. Each edge carries its arrowhead partway along the curve rather than at an end, since most relations point from child to parent and arrowheads at the parent would pile up. Changes are animated: the clicked node stays still, cards glide to their new places, newly shown ones grow out of their parent and hidden ones shrink back into it.

Alt-click a node (or **Focus** in the side panel) to make it the view's only root: the view shows just it and what is under it, unfolded one level. A breadcrumb above the graph shows the trail of notes focused from the top, with **↑ Up** (focus on the note above), **Reset** (the whole tree, folded to the default) and links to each note on the trail. Alt-clicking a note under the focus extends the trail; anything else starts a new one from its shortest path to a top root.

The **Show** menu filters the notes themselves: **In progress**, **Not done**, **Gaps**, **Weak** (low or refuted confidence, a failed or ambiguous outcome), **Changed since…** a date, or **Field…**, any frontmatter field holding a value (or any value). The matches are shown with every note above them up to the roots, faded, for context, and nothing else; folding is set aside, and ctrl-click shows or hides a note's other children. With nothing selected, the side panel lists the matches, most recently changed first. This is the catch-up view for a project: pick the project, then In progress or Not done.

Fold state, focus trail, filters and the project choice are kept in the browser per vault. The toolbar filters by project and type, finds a note (unfolding a path down to it), and folds to the default or unfolds everything.

Selecting a node shows its fields, its relations and its body, with a link to open it in Obsidian (and, for a paper, in Zotero and at its DOI). From there:

- **Connect to…**, then click another node: offers only the relations allowed between the two types, either way round, and not already present;
- **New note here**: a node of any type that can relate to the selected one, created with its relation in one step (so never an orphan). The title is a short name that is also the filename (so no `?` or `:`); the body has one optional box per section of the type, each with a hint of what goes there;
- **Set…** (status, confidence) and **Mark done…** (with an outcome for evidence) on editable notes;
- **×** on a relation removes it, unless either end is done;
- **New root question** adds a question to a project's roots.

Every change runs the matching CLI command (`new`, `link`, `unlink`, `set`, `done`) in the server, so it passes the same checks, and a refusal is shown as that command's error. The server watches `tree/`, `ideas/` and `relations.json` and pushes a new version to the page (server-sent events at `/api/events`) when any changes, so edits made in Obsidian or with the CLI appear at once.

The server listens on 127.0.0.1 only, refuses requests whose `Host` is not `localhost` or `127.0.0.1` (against DNS rebinding), and requires a random per-run token, embedded in the page it serves, on every API call (the `X-Ygg-Token` header, or `?t=` for the event stream, which cannot send headers), so other web pages cannot read or change the tree.

A tree's repository can run `check` before each commit: the main tree has `.githooks/pre-commit`, enabled with `git config core.hooksPath .githooks`.

## Plugin

This repository is a Claude Code plugin, `ygg`, and its own one-plugin marketplace, `yggdrasil`. The plugin is what tells Claude how to work in a tree, so no tree or project repository needs a `CLAUDE.md` for it, and repositories without a tree see none of it.

```bash
claude plugin marketplace add ~/Current_work/repos/yggdrasil    # loads the plugin in place, so edits apply on restart
claude plugin install ygg@yggdrasil
```

| Part | Does |
|---|---|
| `bin/ygg` | The `ygg` command on Claude's PATH. |
| `hooks/session_start.py` | At session start, looks for a tree at or above the working directory, else up to three levels below it. If it finds one, it adds the rules in brief (load `ygg:tree`, change notes only with `ygg`, keep the notebook, offer a handoff) and where the work stands: counts, in-progress and high-priority notes, the last handoff and how many entries followed it. Elsewhere it prints nothing. |
| `ygg:tree` | The working rules: the one rule, commands and allowed relations, runs, superseding, compression, the notebook, and how to write nodes. |
| `ygg:paper` | Adds one paper as a Source (from Zotero) and records what it means for a project as Evidence. |
| `ygg:digest` | Breaks a whole paper, usually one's own, into Questions, Claims and Evidence derived from it, with its Datasets and the open questions of its Discussion. Given the paper's code repository, it also links the script behind each figure as a run Source at the commit matching the paper, which the figure's Evidence derives from; the outputs are not rerun, so the paper stays the Source of the results. |
| `ygg:brainstorm` | Interviews the user to grow a tree: new questions, connections across projects and papers, or a sketch of a new project; writes what is agreed. |
| `ygg:handoff` | Distils the notebook into the tree and writes a handoff entry; on catching up, reads it back with `ygg report --since handoff`. |
