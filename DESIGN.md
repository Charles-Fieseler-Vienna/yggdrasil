# Research Notes Design

> **Status: draft (2026-10-21).** This version moves the format onto the Discourse Graph (DG) Obsidian plugin and TaskNotes frontmatter, managed with `ygg`, which ships as a Claude Code plugin.

## Problem

Computational research produces many experiments and ideas that are interrelated and hard to keep track of. Several projects share questions, methods, datasets and code, so one notes file per project duplicates what they share and has to be kept in step by hand.

The record has to work for ongoing work, not only for finished results: what is being run now, what is blocked, and what is still a guess.

## Protocol

- Every durable tree note is a Question, Claim, Evidence, Source or Dataset.
- Every note has one main idea.
- Relations are typed.
- Uncertainty is explicit.
- Investigations and run groups are represented by Source or Evidence notes rather than requiring individual run nodes.
- Custom node types are allowed when the core four are insufficient. Dataset is the one custom type so far.

## Design

A **tree** is an Obsidian vault of plain Markdown, maintained mainly by Claude through `ygg`. The **main tree** (usually its own repository; `ygg main` says which tree it is) holds only **compressed** nodes: the generalizable questions, claims, evidence and dead ends of each project. Each project keeps its detailed tree in its own repository, in the same format (see [Trees in projects](#trees-in-projects)). This repository, `yggdrasil`, holds no tree: it is the tool, the web app and the Claude Code plugin that teaches Claude the format (see [Plugin](#plugin)). Three standards define the format, and ygg adds only what they lack:

| Layer | Standard | Owns |
|---|---|---|
| Discourse graph | [Discourse Graph Obsidian plugin](https://github.com/DiscourseGraphs/discourse-graph) (`apps/obsidian`) | node types (`nodeTypeId`, `nodeInstanceId`), typed relations (`relations.json`) |
| Work status | [TaskNotes spec](https://github.com/callumalpass/tasknotes-spec) 0.2.0 | `status`, `priority`, `scheduled`, dates, `projects` |
| Research record | this document | `confidence`, `outcome`, evidence references, freezing, project membership, `check` |

A tree is **text only**. Figures, data and code live in project repositories or on the cluster and are referenced, never copied in.

A tree (the main tree, or `research/tree/` in a project):

```text
main-tree/
├── tree/             # every graph node: Question, Claim, Evidence, Source, Dataset
├── ideas/            # project and paper notes: light frontmatter, free prose
├── templates/        # one DG node template per type (written by `ygg init`)
├── relations.json    # every relation; written by the DG plugin or ygg
├── ygg.json          # marks the folder as a ygg tree, with its spec version
├── NOTEBOOK.md       # the lab notebook (project trees; see Notebook)
└── .obsidian/plugins/{discourse-graphs,tasknotes}/data.json   # plugin settings (written by `ygg init`)
```

The tool's own layout, and how to work on it, are in `DEVELOPING.md`.

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
| `title`, `status`, `priority`, `dateCreated`, `dateModified` | all | TaskNotes; `status` and dates required. `ygg` sets `dateModified` when what the note records changes, not for a change to its work state alone (`status`, `priority`, `scheduled`, `out-of-scope` through `ygg set`) |
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
| `origin` | all | `repository@commit:nodeInstanceId` of the note this one was copied from by `ygg seed` |
| `out-of-scope` | all | `true` on a note that belongs in another tree (the main tree, another project); it stays until compression moves it out. `ygg new/set --out-of-scope`, `ygg set --in-scope`; the one field that may change on a done note |

TaskNotes should be set to identify tasks by property (`taskIdentificationMethod: property`, `taskPropertyName: nodeTypeId`, empty value), so every node is a task and project notes are not, without a `#task` tag. The pipeline-specific fields of `obsidian_kanban_ai` (`harness`, `agent`, `skills`, `model`, `cli_args`) and its extra statuses are not used.

### Status and freezing

`status` is the work state: `open` (proposed, not started), `in-progress` (being run or worked on), `done`.

A note is editable while it is `open` or `in-progress`, and frozen once it is committed as `done`, whatever its type. A `done` note is never rewritten; a new note of the same type `supersedes` it. Freezing is judged against the last commit, by `ygg check` and by the commands alike: a note marked `done` since then (by mistake, say) can still be reopened with `ygg set NOTE --status open`, which clears its `completedDate`. A done note copied by `ygg seed` is frozen from the start.

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

A note no project reaches is **in no project**. That is allowed, since a brainstorm leaves loose questions that connect to nothing yet: `check` warns, `ygg report` lists them (also with `--project`), and the web app shows them whichever project is selected. Linking them in, or making them roots, is for later; so is moving out the ones marked `out-of-scope`, which compression does (see [Compression](#compression)).

`## Findings` summarises the project's current conclusions in prose, citing Claims, e.g. `- The head wave is driven at the head ([[CLM - Head wave is driven at the head]]).` It may be revised freely.

## Compression

The main tree holds only compressed nodes. Each project keeps its own detailed tree in its own repository: every step of the logical progression, every small methods question, every diagnostic: a ten-day project easily reaches 50 nodes. Most of it is not useful to other projects.

When a project, or a phase of one, is finished, its detailed tree is **compressed** into a few generalizable nodes. The test for keeping something is whether it is a generalizable conclusion, rather than a narrowly scoped or very specific methods question, claim or result. Compression is a judgement made with the user, not an automatic step.

- As a guide to size, each figure gets at least one Question, and each Claim is about what one to three of its panels demonstrate. Each Claim has its own Evidence note. A 12-panel abstract yields up to about 12 Claims.
- A compressed Evidence note typically summarises an investigation that spanned many runs.
- Compressed Evidence is `derived from` a Source pointing to the detailed tree at a fixed commit, so a new project that needs a detailed method can walk down into it, and from the Dataset it rests on.
- The project's `roots` list the compressed root nodes.
- A project seeded from the main tree (see [Seeding](#seeding)) is mapped back: the outline marks the seeded notes, and **Seeded from this tree** lists what the project related to them, to be written against the originals.
- A tree compressed before is compressed incrementally: the new tree Source supersedes the earlier one, and **Since the last compression** lists the notes, relations and notebook entries that are new or changed since its commit, which the outline also marks.
- Notes the project tree marks `out-of-scope`, and those in no project there, are listed apart: each is moved into the main tree (or noted for another project), dropped, or left. Moving is a new note here, like any compressed note; the project's note stays where it is.
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

A project keeps its detailed tree in its own repository, e.g. `my-project/research/tree/`, made with `ygg init` and opened as its own Obsidian vault. It uses the same types, relations, frontmatter and checks as the main tree, at full granularity: every small run, diagnostic and methods question. That is where day-to-day work is tracked (`status`, TaskNotes boards).

When a project or phase is finished, `ygg compress PATH` (which records into the main tree, wherever it is run) prints the project tree's outline and records it there as a Source at its current commit. The compressed nodes are then written by hand with the user (see [Compression](#compression)).

## Seeding

Work also flows down: a project usually starts from questions in the main tree. `ygg seed NOTE...` (run in the project's tree; `--from TREE` to copy from a tree other than the main tree) copies those notes and everything under them (the same walk as project membership; `--depth N` takes fewer steps down, though a Claim always comes with its Evidence and a note with its Sources) and makes them roots of a project there. Copies are new notes, with new ids, carrying `origin: repository@commit:nodeInstanceId`, so the main tree must be committed. Done notes stay done. Relations among the copied notes are copied; links in bodies to notes left behind become plain text. Seeding again reuses notes already copied, and paper Sources with the same Zotero key or DOI, so it can pull in later main-tree work. A `seed` notebook entry records it. The `ygg:seed` skill then expands the seeded questions into sub-questions and planned runs (open Evidence with Purpose and Method).

The main tree is not changed by seeding; [Compression](#compression) maps the results back.

## Notebook

A project tree has a lab notebook, `NOTEBOOK.md` at its root (made by `ygg init`). It is the raw record under the tree: what was tried, decided, abandoned or guessed, as it happens, before it is settled enough to be a node. Three layers, each a cleaned-up version of the one below:

| Layer | Where | Holds | Written |
|---|---|---|---|
| Notebook | project repository | everything, dated, unedited | as the work happens, by the user and by Claude |
| Project tree | project repository | the graph of settled results, open questions and runs | when something settles |
| Main tree | its own repository | the compressed, generalizable part | at the end of a phase |

Each entry is a `## YYYY-MM-DD HH:MM` heading, optionally `— tag` (`decision`, `dead-end`, `run`, `idea`, `ask`, `answer`, `handoff`), and free Markdown that links nodes as `[[...]]`. Entries are appended, newest last, and never edited or reordered; a correction is a new entry. The one change to a past entry is ticking a to-do's box (see [To-dos, issues and questions for the user](#to-dos-issues-and-questions-for-the-user)). ygg appends each entry in one write in append mode, so concurrent writers do not lose entries, and `ygg init` marks `NOTEBOOK.md` `merge=union` in `.gitattributes`, so git merges two machines' appends by keeping both. `ygg log` appends one; `ygg check` warns, without failing, about links to notes that do not exist. ygg never rewrites the notebook; to tick a box it overwrites that one character in place.

There is no separate decision log. A decision is first an entry; once it holds, it becomes a Claim (about a method, if it is one) with its Evidence, which may cite the entry's date.

A **handoff** is an entry tagged `handoff`: where things stand, what is running (job IDs, output paths), the next steps as links to nodes, and loose state only the session knows (uncommitted code, scratch paths). Before writing one, the notebook since the last handoff is distilled into the tree: runs, results, decisions and dead ends become nodes, and the next one to three notes get `priority: high`. To catch up, `ygg report --since handoff` lists the high-priority and in-progress notes, the notes changed and the notebook entries since the last handoff. The `ygg:handoff` skill does both. Every tree has a notebook, the main tree too: brainstorms there end with a `brainstorm` entry of what was set aside and the threads left open.

### Runs

Most runs are logged first and only some become nodes; many are dropped after a pivot. A run is therefore recorded in the notebook, not in a node: `ygg log "lag sweep, 1-8 s" --pid 41233 --pid 41240 --log results/lag.log` appends an entry (tagged `run`) ending in one standard line,

```
run r261022-41233 · pids 41233, 41240 · host lab-ws3 · logs results/lag.log
```

with the host filled in, `jobs 123456` for cluster jobs (`--job`), and `for [[EVD - ...]]` when the run serves a note that already exists (`--for`). Without `--pid` or `--job`, `--for NOTE` just adds `for [[NOTE]]` to the entry, for a decision or dead end about that note. The id (`r` + date + first PID or job) is how everything else refers to the run. A run counts as **looked at** once anything after it mentions its id: a node's body (the Method of the Evidence it became, or a run Source), a later notebook line ("r261022-41233: loss plateaued, nothing new"), or a `dropped` entry; or once its `for` note is done. Only runs since the last handoff are expected to be looked at: the handoff sums up the loose ones, and older runs stay in the notebook as plain record. `ygg drop ID... -m "why"` (with `--kill` to stop its processes here) gives a run up: it appends a `dropped` entry ending in `dropped ID, ...`, after which nothing flags the run.

What can be checked is checked deterministically, on the run's own host only: whether each PID still runs and when each log was last written. A PID is checked through `/proc` where it exists, else `ps` (macOS has no `/proc`), else `kill -0`; a zombie (exited, not reaped) counts as ended, and so does a process that started after the run was logged, since its PID was reused. When nothing can tell, as in a sandbox that hides other processes, the run is "not checkable here", never "ended". Cluster jobs and runs on other hosts are listed, not checked; a container usually has its own hostname, so runs logged inside one count as on another host. `ygg log --pid` checks the PID: one that has exited, or is the shell running `ygg` itself (what `pgrep -f PATTERN` finds first, since the shell's command line holds the pattern; and `$!` after `setsid`, which forks, has exited), is replaced by the process writing the run's `--log`, found in `/proc` (or, for a job started with `setsid`, the leader of its session, which runs until every step of the job is done); failing that, it warns. Log paths are resolved where `ygg log` runs and stored relative to the tree's repository (absolute when outside it), so they mean the same on every clone. `ygg report` and the session hook give one summary line and a **Needs action** group: an ended run that nothing mentions yet, if it was logged since the last handoff, or `for` a note that is not done (whenever it was logged), and a running one whose logs have been quiet for two hours. `ygg runs` lists the runs still running or waiting to be looked at, with their logs (`--all` for every run, `ygg runs NOTE` for one note's), and `ygg show NOTE` lists a note's runs.

`ygg watch [ID | NOTE ...]` blocks until the logged runs running on this machine (or those named) end, printing one line per event: a run ended (with the last lines of each of its logs, `--tail N`, 5 by default, as a terminal shows them, so a progress bar gives its final state), its log printed a failure (a Traceback, an `...Error`, Killed, out of memory, `nan`...; new lines only), or its log went quiet; then the Needs action lines. It replaces an agent's own wait-then-read loop, and `ygg log --pid` says so when it logs a run. It is plain output, so any agent harness can run it in the background and be woken when it returns (`--first` to return at the first end, `--timeout HOURS`). It ends with the session that started it; the next session starts it again if runs are still going.

### To-dos, issues and questions for the user

A **to-do** is a Markdown task line in any entry, `- [ ] text`, which Obsidian and GitHub render as a checkbox; it is done once ticked, `- [x]`. `ygg log [TEXT] --todo "..."` (repeatable) writes them, alone or under the entry's text; `ygg tick TEXT [-m NOTE]` ticks the one open to-do containing TEXT (refusing if none or several do), and with `-m` appends a `done` entry saying what came of it. `ygg report` lists the open to-dos, newest first, and the session hook counts them. To-dos are the notebook's small next steps; a next step that is itself an experiment is a planned Evidence note instead.

An **issue** is a problem found in something results rest on: a bug in the code, bad frames in a recording, a wrong preprocessing step in a Dataset. Invalidating everything downstream would usually throw away more than the problem touches, so an issue is a to-do that ygg follows through the tree:

```
- [ ] issue i261022-1 · affects [[DATA - 36-animal cohort]], [[@Stage 2 run]]
```

`ygg log "two recordings have all-NaN Hilbert features" --issue --affects NOTE` (repeatable) writes it and prints its id (`i` + date + a counter). The notes **resting on** the affected ones are what derive from them, the claims their evidence supports or opposes, and the questions following from those claims, recursively; `ygg impact NOTE...` lists them for any notes, and `ygg issues [ID] [--all] [--notes]` lists the open issues with how many of those notes are still to judge. Each one is judged, partly by the agent and partly by the user, in one of two ways:

- **redone**: a new note supersedes it, made after the issue was logged (a note that replaces another under the issue, or is made after the issue, needs no judging itself);
- **unaffected**: a later notebook line names the issue id and the note, saying why (`i261022-1: [[EVD - ...]] uses no Hilbert features`).

A fixed Dataset is a new Dataset note superseding the old one. `ygg resolve ID... -m "how"` closes issues once judged: it appends a `resolved` entry ending in `resolved ID, ...` and ticks the issue's box, warning about any note not yet judged. A ticked box alone also counts as resolved. Open issues are listed in `ygg report`, in the session hook, and in the web app, where each note still to judge carries a badge.

A **question for the user** is a decision the agent should not make alone: scope, a definition, go or no-go on a result that sits on its bar. Left in handoff prose ("your call: ..."), such questions were restated, reworded and lost from one session to the next, and nothing knew when one was answered; so a question is a line too, with an id, the notes it is about, and the notes whose work waits for the answer:

```
- [ ] ask a261022-1 · on [[CLM - Steering passes both S1 bars]] · blocks [[EVD - Stage 5 neural test]] · Adopt the new definition?
```

`ygg log [TEXT] --ask "QUESTION" [--on NOTE] [--blocks NOTE]` (both repeatable) writes it, under the entry's text, which gives the context, and prints its id (`a` + date + a counter). `ygg asks [--all]` lists the open ones (with `--all`, the answered ones and their answers). The user answers with `ygg answer ID -m "TEXT"`, or in the web app, which runs it: an `answer` entry holding the answer and ending in `answered ID`, with the question's box ticked (a box ticked by hand also closes it, with no answer recorded). A change of mind is a new entry, not a second answer. `ygg log` warns when an entry leaves a decision to the user in prose ("You: accept or reject ...", "your call", "awaiting the user") without asking a question or referring to one waiting (by its id, or as a question), judged line by line; the session briefing repeats the warning for the last handoff, so the next session asks it.

Open questions lead `ygg report` (**Waiting on the user**), the session hook and the web app's Overview, and `ygg show` lists them on their notes; a note a question blocks is marked "waiting on the user" on the agent's list, so it is not started. Questions answered since the last handoff (by position in the notebook) are listed next (**Answered since the last handoff: act on these**), and the notes they name join the agent's list, so the next session finds and acts on them; the handoff after that settles them into the tree, and they drop off.

**The agent's list** (what a session looks at first) is ordered, most important first, in the session hook, `ygg report` and the web app alike: the notes named by a question answered since the last handoff, then those in progress, then those at high priority, then those named in the last handoff (by the first that applies; ties by filename). A note that waits on something, an unfinished note it is `blocked-by` or a question for the user, is **blocked**: it is listed after the rest, unnumbered (under "Blocked, not to start until what blocks them is done or answered"), with what blocks it among its reasons, and cannot be ordered. The user can put notes first: `ygg order NOTE...` (or the web app's **Change order**) appends an `agenda order` entry numbering them, and the latest such entry puts those notes first, in its order, with the rest after them in the default order; a note that has left the list is skipped. `ygg order --default` appends an entry with no numbered notes, which returns to the default order. Only notes on the list, and not blocked, can be ordered. Each change appends an entry, like every other notebook write, and the latest is in force; a change to the order already in force writes nothing.

**Findings not yet in the tree.** The notebook is the raw record; when a session runs for days without a handoff, results that settle or overturn notes can pile up there while the notes stay as they were. Entries since the last handoff that record findings (any tag but `run`, `handoff`, `agenda order`, `todo`, `ask`, `answer`, `issue`, `resolved`, `done`, `dropped`, `seed` and `brainstorm`) and are newer than the latest `dateModified` of any note and the latest relation added are counted, comparing times across time zones (a note's offset; the notebook's stamps in this machine's zone); from eight on, the session hook, `ygg report` (under **Needs action**) and the web app's Overview say to distil them (the `ygg:handoff` skill's step 2), and `ygg log` says so at every eighth.

## Workflows

There are two ways of working, joined by seeding and compression. Both use the same trees, commands and notebook; a "main tree" is only a tree used for brainstorming across projects. They are kept here so that changes to one part of ygg keep both working end to end.

### Brainstorming

Thinking about what to work on, without code: a conversation that ends in notes (`ygg:brainstorm`). It happens mostly in the main tree, but also as a break within a project's heavy computation, in the project's tree; "main tree" names how a tree is used, not a different kind of tree, and every tree has the same commands and notebook.

- **Input**: an idea, a result from a project, a paper, a talk. Papers come in as Sources linked to Zotero, with Evidence for what they mean here (`ygg:paper`), or broken down whole when they are to be built on (`ygg:digest`).
- **Output**: open Questions connected to what is already known, especially across projects; links between existing notes; sometimes a new project note with root questions. No runs and no Evidence of our own, so few Claims.
- **Rhythm**: occasional sessions, each closed with a `brainstorm` notebook entry (what was considered and set aside, and why; the threads left open), `ygg check` and a commit. The notes are the record of what was kept, the notebook of what was not.
- **Ends** when a question is ready to pursue: it is seeded into a project's tree. A brainstorm inside a project writes only to the project's tree, even ideas that belong elsewhere: they may be left in no project and marked `out-of-scope`, and move out at compression, never during the brainstorm.

### A coding project, in the project's tree

Day-to-day work in a project repository, mostly runs and analyses, with an agent writing code alongside the user.

1. **Seed** the tree from the main-tree question (`ygg seed`), and **expand** it into sub-questions and planned runs, open Evidence saying what to run and what would answer it (`ygg:seed`).
2. **Work** in sessions: runs (below), notebook entries for decisions, dead ends and surprises as they happen (`ygg log`), and nodes only once something settles. Most of the notebook never becomes nodes. Commits are frequent.
3. **Hand off** at the end of each session and catch up at the start of the next (`ygg:handoff`): the notebook since the last handoff is distilled into nodes, loose runs are summed up, and the next steps get `priority: high`.
4. **Compress** at the end of a phase (`ygg compress`, in the main tree): the generalizable results, dead ends and open questions go back up, written against the notes the project was seeded from, along with the notes marked out of scope there. A later compression shows only what changed since. New questions from it are brainstorming again.

### The life of a run

Runs are launched and logged first; a node comes later, if at all. Each one ends in one of three ways.

- **Logged**: on launch, `ygg log "lag sweep, 1-8 s" --pid N --log PATH`, with `--for "EVD - ..."` when it was planned as a note (the post-Bash hook reminds an agent that forgets). It prints the run id. `ygg watch` in the background, in any agent harness, returns when runs end and reports failures and quiet logs on the way; a later session sees them in the session hook, `ygg report` and `ygg runs`.
- **Becomes evidence**, when the result matters: a run Source (`--run repository@commit:path`, the commit the run used) and the Evidence derived from it, its Method citing the run id, then `ygg done`.
- **Noted**, as most are: one notebook line citing the run id ("r261022-41233: no gain over ridge"), often in the handoff entry.
- **Dropped**, as many are after a pivot or a bug: `ygg drop ID... -m "why"` (`--kill` stops it), and nothing flags it again. A planned Evidence note that will now never get its result is not left open: finish it with outcome `failed` or `promising-out-of-scope` when the reason is worth knowing, else lower its priority or supersede it with the new plan.

Any mention of the run id after it was logged marks it looked at. Runs nobody mentions are flagged only until the next handoff; after that they stay in the notebook as plain record.

### A bug in data or code

A problem found in something results rest on is rarely a reason to redo everything below it, but every result below it has to be judged.

1. **Log it** as an issue as soon as it is found, naming the notes it touches: `ygg log "..." --issue --affects "DATA - ..."`. Fixing it may come later; the record comes first.
2. **See what rests on it**: `ygg issues ID` lists every note to judge, with the path that puts it there.
3. **Judge each note**, the agent proposing and the user deciding: rerun what the problem could change and supersede the old note with the new one (a fixed Dataset supersedes the old Dataset); for what it cannot change, write one notebook line naming the issue id and the note, with the reason. Runs for it are logged as usual.
4. **Resolve** the issue when nothing is left to judge: `ygg resolve ID -m "how"`.

Superseded notes stay in the tree as record. The web app hides them by default and shows the new note in their place.

## Tooling

`scripts/ygg` is the only writer of notes and `relations.json` besides the Obsidian plugins' own UIs. It finds its tree by looking for `ygg.json` from the current directory up, else, inside a git repository, in its subfolders up to three levels down as the hooks do (using the one tree found there, and naming it on stderr; several are an error), or takes `--vault PATH`. The Claude Code plugin puts it on Claude's PATH as `ygg` (`bin/ygg`); for your own shell, `ln -s "$PWD/bin/ygg" ~/.local/bin/ygg`.

It is a [uv](https://docs.astral.sh/uv/) script: its first lines declare Python 3.10+ and the web app's dependencies (FastAPI, uvicorn, watchfiles), and running it directly lets uv provide them. Every command but `serve` is standard library only, so `python3 scripts/ygg ...` also works where uv is missing. `bin/ygg` uses uv only for `serve` and runs everything else on `python3`.

| Command | Does |
|---|---|
| `ygg init [PATH] [--project TITLE] [--main]` | Makes PATH a tree: folders, `ygg.json`, `relations.json`, templates, plugin settings; `--main` also makes it the main tree. Safe to rerun; it upgrades settings in place. |
| `ygg new TYPE TITLE [--link REL:NOTE] [--link-from REL:NOTE] [--body FILE|-] ...` | Creates a node (`TYPE` is a node type) or a project note (`project`, with `--root`). |
| `ygg link SOURCE REL TARGET` / `ygg unlink ...` | Adds or removes a relation. |
| `ygg set NOTE [...]` | Changes fields or the body of an editable node, or a project's roots. |
| `ygg done NOTE [--outcome X]` | Finishes and freezes a node. |
| `ygg show NOTE` | Prints a note with its relations (and a claim's datasets), or a project with its members. |
| `ygg report [--project P] [--since DATE\|handoff] [--all]` | Lists the questions waiting on the user and those answered since the last handoff, then the agent's list in its order, then high-priority and in-progress work, open nodes, unanswered questions, low-confidence claims, notes in no project, and notes out of scope (apart from the work lists). A superseded note is left out of the work lists, since a newer note has taken over its work; one not yet done is listed once more at the end. With `--since`, also the notes changed and the notebook entries since then; then the open to-dos and open issues. Kept short: empty groups are left out and each lists its first 8 notes (`--all` for every one); runs get one summary line and a **Needs action** group (see [Runs](#runs)). |
| `ygg log [TEXT] [--tag WORD] [--handoff] [--body FILE|-] [--pid N] [--job ID] [--log PATH] [--for NOTE] [--todo TEXT] [--issue --affects NOTE] [--ask QUESTION --on NOTE --blocks NOTE]` | Appends a dated entry to the notebook (see [Notebook](#notebook)); with `--pid` or `--job`, logs a run and prints its id (see [Runs](#runs)); `--todo` adds to-do lines, `--issue` an issue line, `--ask` a question for the user (see [To-dos, issues and questions for the user](#to-dos-issues-and-questions-for-the-user)). |
| `ygg tick TEXT [-m NOTE]` | Ticks the one open to-do containing TEXT. |
| `ygg issues [ID] [--all] [--notes]` | Lists open issues and the notes resting on what they affect, judged or still to judge. |
| `ygg impact NOTE...` | Lists the notes that rest on these, and how. |
| `ygg resolve ID... [-m HOW]` | Closes issues, warning about notes not yet judged. |
| `ygg asks [--all]` | Lists the questions waiting on the user (with `--all`, the answered ones too). |
| `ygg answer ID -m TEXT` | Answers a question for the user, in a new notebook entry, and ticks its box. |
| `ygg order NOTE... \| --default` | Puts notes first on the agent's list, in this order, in a new notebook entry; `--default` returns to the default order. |
| `ygg runs [NOTE] [--all]` | Lists the runs still running or waiting to be looked at, with their logs. |
| `ygg drop ID... [-m WHY] [--kill]` | Gives runs up, so nothing flags them again. |
| `ygg watch [ID\|NOTE...] [--first] [--timeout H] [--tail N]` | Waits for runs to end, printing a line per end (with the end of its logs), failure or quiet log. |
| `ygg sync` | Regenerates `projects:` and fills in TaskNotes dates missing from notes made in Obsidian. |
| `ygg main [PATH]` | Prints the main tree; with PATH, sets it (see [The main tree](#the-main-tree)). |
| `ygg compress PATH [--dry-run]` | Outlines a project tree and records it as a Source at its commit, in the main tree (or `--vault`); refuses uncommitted trees. Maps seeded notes back, lists notes out of scope or in no project there and, the second time, lists what changed. |
| `ygg seed NOTE... [--from TREE] [--project P] [--depth N] [--dry-run]` | Copies notes and everything under them from another tree into this one (see [Seeding](#seeding)). |
| `ygg serve [--port N] [--open]` | Serves a local web app for browsing and editing the tree (see [Web app](#web-app)). |
| `ygg check` | Validates everything; exits 1 on any error. |
| `ygg schema [--out FILE]` | Prints the schema as a DG export file. |
| `ygg --version` | Prints the tool version and the tree format it writes. |

Notes are named by filename, by the content after the type prefix, by `nodeInstanceId`, or by any unique part of the filename; a whole filename, content or project id in other capitals counts as whole (`BarlowTrack` names the project `barlowtrack`, even where it is part of many filenames).

`check` enforces:

- frontmatter fields and values as above, TaskNotes' required fields, and `completedDate` on `done` notes;
- filenames carry their type's prefix, and `title`, if present, equals the filename;
- every relation in `relations.json` connects existing nodes with an allowed type pair, with no duplicates;
- `derived from`, `follows from` and `supersedes` contain no cycles;
- `done` Evidence has an `outcome` and non-empty Conclusion and Caveats; `done` Questions and Claims have their main section;
- every Claim is supported by at least one Evidence note;
- `projects:` matches the computed membership (a note in no project is a warning, not an error);
- `done` notes are unchanged since `HEAD` (bar `projects:` and `dateModified`), and relations touching them were not removed;
- `run`, `tree` and `figures` are immutable references; only `.md` files are in `tree/` and `ideas/`;
- the DG settings hold the ygg types and no sync password, and `ygg.json` is in the tool's tree format.

### The main tree

Which tree is the main tree is a setting of the user's, one per machine, not part of any tree: `ygg main PATH` (or `ygg init PATH --main`) writes it to `$XDG_CONFIG_HOME/ygg/config.json` (by default `~/.config/ygg/config.json`), and `$YGG_MAIN_TREE` overrides it. `ygg main` prints it, and fails when none is set or it is no longer a tree (moved, say), as do the commands that default to it; a garbled setting counts as none. `ygg seed` copies from it unless given `--from`, and `ygg compress` records into it unless given `--vault`; neither works on a tree with itself. The session hook names it, or says to ask the user and set it.

### Versions

The tool version (`ygg --version`, also in `.claude-plugin/plugin.json`) and the tree format (`spec_version` in `ygg.json`) are separate. The format changes only when a tree written by a new ygg could fail an older one's checks; `ygg init` upgrades a tree in place, and every command warns about a tree in another format (an older one: run `ygg init`; a newer one: update ygg). New optional fields that older versions ignore, like `origin` and `out-of-scope`, do not change the format. Format 2 (ygg 0.3.0) allows notes in no project, which format 1 rejected. `CHANGELOG.md` records both.

### Web app

`ygg serve` serves a web app at `http://localhost:8765/` (`--port`, `--open` to open the browser) until Ctrl-C.

Its first job is transparency: the user sees the project's history and its next steps, and everything the CLI and hooks put in front of the agent as work to do is visible here too, built by the same functions. Steering (changing priorities, ticking to-dos, adding and linking notes) comes second, and every change still goes through `ygg`.

It runs locally and needs the network for its libraries. How it is built is in `DEVELOPING.md`.

The tree is drawn left to right parent → child: questions lead to their follow-ups, claims and informing evidence, claims to their evidence, evidence to its sources and datasets. Arrowheads mark each relation's real destination. Node colour is the type; the border marks gaps (red: a question nothing addresses or informs, a claim nothing supports, done evidence derived from nothing; planned evidence, not yet done, is not a gap), open or in-progress notes (dashed blue), weak ones (double yellow) and out-of-scope ones (dotted grey, faded). Notes in no project are shown whichever project is selected.

Folding is per node. Ctrl-click (Cmd-click on a Mac) a node to fold or unfold what is under it; a node is shown if it is a root or under an unfolded shown node, so a node shared by several parents appears as soon as any of them is unfolded. A folded node shows how many notes and gaps it hides; hidden gaps also tint it red. By default only the top questions are unfolded.

The layout is a tidy tree, one column per level, with each node's children in a fixed order (by filename, so claims, then evidence, then follow-up questions). It is redone on every change, so unfolding a node only pushes what is below it down, and nothing is reordered. A node with several shown parents sits under the shallowest one, and keeps that place while it stays shown, so unfolding another of its parents does not move it; its other edges are still drawn. Each edge carries its arrowhead partway along the curve rather than at an end, since most relations point from child to parent and arrowheads at the parent would pile up. Edges leave a card's right side and enter the next column's left side; between two cards in one column (a `blocked-by` between siblings, say), the edge runs from the bottom of the upper card to the top of the lower one when they are neighbours, with the arrowhead in the gap and the label beside it, and loops out and back in on the right side when other cards sit between them. `blocked-by` edges are dashed, thicker and orange-red. Changes are animated: the clicked node stays still, cards glide to their new places, newly shown ones grow out of their parent and hidden ones shrink back into it.

Dragging a card moves it; it keeps that offset from its place in the layout through later changes and reloads (kept in the browser per vault), until **Reset positions**, at the right end of the toolbar while any card is moved, puts every card back. Dragging the background, or dragging anywhere with the middle button, pans the view; a click (moving less than 4 px) still selects.

Alt-click a node (or **Focus** in the side panel) to make it the view's only root: the view shows just it and what is under it, unfolded one level. A breadcrumb above the graph shows the trail of notes focused from the top, with **↑ Up** (focus on the note above), **Reset** (the whole tree, folded to the default) and links to each note on the trail. Alt-clicking a note under the focus extends the trail; anything else starts a new one from its shortest path to a top root.

With nothing selected, the side panel is the **Overview** (also the toolbar button), where things stand as the agent is told it:

- **Waiting on you**: the open questions for the user, each with its context, the notes it is about and blocks, and a box to answer it (`ygg answer`); below them, the questions **answered since the last handoff**, which the next session is told to act on;
- **What the agent sees first**: the agent's list, numbered in its order (see [To-dos, issues and questions for the user](#to-dos-issues-and-questions-for-the-user)): the notes in progress, at high priority and not done (unless superseded), named in the last handoff, or under a question answered since; a note an open question blocks is marked "waiting on the user". A line says whether the order is the default or partly the user's; blocked notes follow, with a dash for a number. Each note has a priority menu, so setting a note to high puts it on the list, and lowering it takes it off. A numbered row is dragged by its ⠿ grip (or moved with ↑ ↓, shown on hover) to reorder the list; once it differs, **Save order** runs `ygg order` with the numbered notes and **Cancel** drops the change, and **Default order** (shown while the user's order applies) runs `ygg order --default`;
- the open **to-dos** of the notebook, newest first, each with a box that ticks it (`ygg tick`);
- the open **issues**, each with the notes still to judge;
- **runs**: the summary line and the Needs action lines;
- the **last handoff**, rendered, and the latest notebook entries;
- the agent's **briefing**, word for word as the SessionStart hook gives it, folded away.

Answers are the one notebook entry written here; the rest of the notebook is written with `ygg log`.

The **Show** menu filters the notes themselves: **Waiting on you** (the notes open questions are about or block), **What the agent sees first** (as above), **Frontier**, **In progress**, **Not done**, **Gaps**, **Out of scope**, **Weak** (low or refuted confidence, a failed or ambiguous outcome), **Changed since…** a date, or **Field…**, any frontmatter field holding a value (or any value). The matches are shown with every note above them up to the roots, faded, for context, and nothing else; folding is set aside, and ctrl-click shows or hides a note's other children. With nothing selected, the side panel lists the matches, most recently changed first; under **What the agent sees first** it is that list instead, as in the Overview and reordered the same way, and each card carries its number (a dash if blocked). This is the catch-up view for a project: pick the project, then In progress or Not done.

**Frontier: the ways forward** turns the view around. Instead of everything from the roots down, it shows only the notes that are open or in progress, and the gaps, leaving out superseded notes and those at priority `none`. Done notes are removed, not faded. A note whose parents are all done becomes a root, says on its card which done note it comes after, and the roots are ordered high priority first, then in progress, then under an open issue. Clicking through to a note that is not on the frontier returns to the whole tree.

**Superseded** notes are a toggle beside the types, off by default: while they are hidden, the note replacing each takes its place, with its parents and children, so the tree shows the current state. Shown, they are faded and struck through. Notes still to judge under an open issue carry a purple **!** badge (the panel says which issue and what to do), and the **Under an open issue** filter finds them. High-priority notes carry an orange **▲** badge, and notes with an open question for the user a teal **?** badge, whose panel has the question and a box to answer it.

Fold state, focus trail, filters and the project choice are kept in the browser per vault. The toolbar filters by project and type, finds a note (unfolding a path down to it), and folds to the default or unfolds everything.

Selecting a node shows its fields, its relations and its body, with a link to open it in Obsidian (and, for a paper, in Zotero and at its DOI). From there:

- **Connect to…**, then click another node: offers only the relations allowed between the two types, either way round, and not already present;
- **New note here**: a node of any type that can relate to the selected one, created with its relation in one step (so never an orphan). The title is a short name that is also the filename (so no `?` or `:`); the body has one optional box per section of the type, each with a hint of what goes there;
- a **priority** menu in the fields, which applies at once, and **Set…** (status, confidence) and **Mark done…** (with an outcome for evidence) on editable notes;
- **×** on a relation removes it, unless either end is done;
- **New root question** adds a question to a project's roots.

Every change runs the matching CLI command (`new`, `link`, `unlink`, `set`, `done`, `tick`, `answer`, `order`) in the server, so it passes the same checks, and a refusal is shown as that command's error. The server watches `tree/`, `ideas/`, `relations.json` and `NOTEBOOK.md` and pushes a new version to the page (server-sent events at `/api/events`) when any changes, so edits made in Obsidian or with the CLI appear at once.

The server listens on 127.0.0.1 only and accepts only API calls carrying a random token embedded in the page it serves, so other web pages cannot read or change the tree.

A tree's repository can run `check` before each commit: the main tree has `.githooks/pre-commit`, enabled with `git config core.hooksPath .githooks`.

## Plugin

This repository is a Claude Code plugin, `ygg`, and its own one-plugin marketplace, `yggdrasil`. The plugin is what tells Claude how to work in a tree, so no tree or project repository needs a `CLAUDE.md` for it, and repositories without a tree see none of it.

```bash
claude plugin marketplace add Charles-Fieseler-Vienna/yggdrasil   # or a local clone's path, which loads it in place
claude plugin install ygg@yggdrasil
```

| Part | Does |
|---|---|
| `bin/ygg` | The `ygg` command on Claude's PATH. |
| `hooks/pre_bash.py` | Before a Bash command, in a repository with a tree: stops a wait loop polling `pgrep -f PATTERN`, which never ends because the loop's own shell has the pattern in its command line, and points to `ygg watch`, a loop on `kill -0 PID`, or a pattern opening with a bracket class. It also refuses `ygg ... --confidence high` (or `refuted`) from a subagent (the hook input carries `agent_id`): a subagent writes at most `medium` and argues for more in its report, and the main session raises it after review. Silent elsewhere. |
| `hooks/post_bash.py` | After a Bash command, in a repository with a tree: if it runs or writes a script (`.py`, `.R`, `.jl`, `.sh`) at a path outside the repository, such as `/tmp`, reminds Claude that a script whose output feeds a result belongs in the repository, committed and cited as `repository@commit:path`; if it launched a run (`nohup`, `sbatch`, a trailing `&`, a background command...), reminds Claude to log it with its PID, host and logs; if it committed and the notebook has no entry from the last 20 minutes, reminds Claude to log any decision or result. Silent elsewhere. |
| `hooks/session_start.py` | At session start, looks for a tree at or above the working directory, else, inside a git repository, up to three levels below it (so a session in `~` announces no tree). If it finds one, it adds the rules in brief (load `ygg:tree`, change notes only with `ygg`, keep the notebook and log runs, put findings that settle or overturn notes into them during the session and log an issue on a note a finding shows wrong, offer a handoff, brainstorm, seed and compress) and where the work stands: counts, in-progress and high-priority notes, the last handoff and how many entries followed it (and a decision it leaves to the user in prose, to ask now), open issues and the number of open to-dos, the runs named since, findings piling up in the notebook unrecorded in the notes, uncommitted changes in the tree (the sign of a session that stopped before recording its work), and a tree in another format. The web app's Overview shows the same, word for word. Elsewhere it prints nothing. |
| `ygg:seed` | Starts a project tree from main-tree questions with `ygg seed`, then expands them into sub-questions and planned runs. |
| `ygg:tree` | The working rules: the one rule, commands and allowed relations, runs, superseding, the notebook, and how to write nodes. |
| `ygg:paper` | Adds one paper as a Source (from Zotero) and records what it means for a project as Evidence. |
| `ygg:digest` | Breaks a whole paper, usually one's own, into Questions, Claims and Evidence derived from it, with its Datasets and the open questions of its Discussion. Given the paper's code repository, it also links the script behind each figure as a run Source at the commit matching the paper, which the figure's Evidence derives from; the outputs are not rerun, so the paper stays the Source of the results. |
| `ygg:brainstorm` | Interviews the user to grow a tree: new questions, connections across projects and papers, or a sketch of a new project; writes what is agreed. |
| `ygg:compress` | Compresses a project tree into the main tree with `ygg compress`: the outline, papers already there, notes seeded from the main tree (written against their originals), out-of-scope notes, and on a second compression only what changed. |
| `ygg:handoff` | Distils the notebook into the tree and writes a handoff entry; on catching up, reads it back with `ygg report --since handoff`. |
