# Research Notes Design

## Problem

I have a ton of computational experiments and ideas, and they are interrelated and hard to keep track of. For example, multiple projects now share semi-organized nodes:

- `research/FRAMEWORK.md`
- `research/SSL_ALIGNMENT.md`
- future projects such as fly/mouse decomposition, the data repository, and `barlow_track`

Maintaining one file per project would duplicate shared nodes and require project interfaces to be updated manually.

## Design

Use a separate Git repository containing plain Markdown files. It may be opened as an Obsidian vault, but Obsidian is optional.

The repository is mainly maintained by Claude (see `CLAUDE.md`). Note creation and modification go through `scripts/notes.py`, so the format stays machine-checkable.

The repository is **text only**. Figures, data and code live in project repositories or on the cluster and are referenced, never copied in.

```text
yggdrasil/
├── tree/            # experiments and decisions: the frozen record
│   ├── high-res-innovation-diagnostic.md
│   ├── non-contrastive-losses-only.md
│   └── ...
├── ideas/           # projects and hypotheses: the living synthesis
│   ├── control-decomposition.md
│   ├── head-wave-hypothesis.md
│   └── ...
├── scripts/
│   ├── notes.py
│   └── hooks/pre-commit
├── CLAUDE.md
└── DESIGN.md
```

### Note types

| Type | Folder | What it is | Mutable? |
|---|---|---|---|
| `experiment` | `tree/` | One computational run: why, what was run, results, and its conclusion. | Until `done`; then frozen. |
| `decision` | `tree/` | A choice that shapes later work: context, the decision, rationale, alternatives. | Until `done`; then frozen. |
| `hypothesis` | `ideas/` | A single question or prediction, smaller than a project. | Always. |
| `project` | `ideas/` | One page per project: summary and current findings. | Always. |

### `tree/`: experiments and decisions

Experiments are the research record. Each one states its own conclusion, and once it is `done` the note is frozen. A conclusion is never rewritten; a later experiment `supersedes` it.

Decisions record choices that are bigger than a single finding: a loss family, what goes into a model, which data to use. A decision is `open` while it is proposed or waiting on the user, and `done` once made; then it is frozen too, and a later decision `supersedes` it. Decisions are usually `motivated_by` the experiments that prompted them, and later experiments `depends_on` them.

Every experiment and decision is `part_of` at least one project, and may be part of several.

### `ideas/`: projects and hypotheses

Each project page has a `## Findings` section: the project's current conclusions, each citing the experiments it rests on with inline links. Findings are coarser than experiments: one finding usually rests on several experiments, and many small experiments are never cited directly. For example: `The head wave is driven at the head ([[high-res-innovation-diagnostic]]).` Findings may be revised as understanding changes, because the evidence they cite is frozen; Git history keeps earlier versions.

Each project page also has a `## Decisions` section linking the decisions that shape the project. Small practical decisions need not be listed there by hand: they are `part_of` the project, so they appear in the graph, the backlinks panel and the section's Dataview block.

Hypotheses are short notes that are `part_of` a project. Whether a hypothesis has been tested, supported or contradicted is read off the experiments that link to it.

Project pages do not list their experiments and hypotheses by hand. Obsidian shows them in the backlinks panel, and each project page has optional Dataview blocks that list them live. Cross-project interfaces are simply the experiments that are `part_of` both projects.

Narrative tied to one codebase (papers in progress, documents such as `FRAMEWORK.md`) stays in that project's repository. It cites note IDs rather than duplicating the research record.

### Nothing gets lost

`scripts/notes.py check` fails if:

- an experiment or decision is not `part_of` any project;
- a `done` experiment has an empty `## Conclusion`.

So every finished experiment's conclusion is written down, and every experiment is reachable from a project page through the graph, the backlinks panel and the page's Dataview list. Experiments can therefore be granular; they do not each need a place in the Findings.

`notes.py report` lists finished experiments that no project's Findings cite. It is a prompt for reviewing whether the Findings are current, not a requirement.

## Frontmatter

Frontmatter holds only scalar fields and simple lists. Links live in the body (see [Links](#links)).

```yaml
---
id: high-res-innovation-diagnostic   # equals the filename; never changes
type: experiment                     # experiment | decision | hypothesis | project
title: "High-res innovation diagnostic"
status: done                         # open | done
outcome: succeeded
created: 2026-10-12
run_start: 2026-10-10T14:02
run_end: 2026-10-11T03:40
run: Cosyne_2027@eabf5bd:scripts/run_highres_innovation.sh
data:
  - /cluster/project/results/highres_innovation/
figures:
  - Cosyne_2027@eabf5bd:paper/figures/fig2_innovation.pdf
refs:                                # Zotero / BibTeX citation keys
  - wen2012proprioceptive
legacy_ref: "TREE 1.12"
---
```

| Field | Allowed on |
|---|---|
| `id`, `type`, `title`, `created`, `refs`, `legacy_ref` | all |
| `status` | experiment, decision |
| `outcome`, `run`, `run_start`, `run_end`, `data`, `figures` | experiment |

`status` is `open` or `done`. `outcome` is required once an experiment is `done`; decisions have no outcome:

```text
succeeded
failed
ambiguous
promising-out-of-scope
```

"Superseded" is not stored. It is derived from a later note's `supersedes` link.

Experiment bodies have the sections `Purpose`, `Method`, `Results`, `Conclusion` and `Caveats`. `Conclusion` is required before `done`.

Decision bodies have the sections `Context`, `Decision`, `Rationale` and `Alternatives considered`. `Decision` is required before `done`.

## Links

Links live in a `## Links` section at the end of the body, grouped by relation, each with an optional one-line annotation:

```markdown
## Links

### part_of
- [[control-decomposition]]
- [[ssl-alignment]]

### supports
- [[head-wave-hypothesis]] — innovation peaks at head segments
```

The relation is a heading, not a YAML key, so a note can have any number of links of any type. Because they are ordinary wikilinks in the body, Obsidian's graph view and backlinks panel work without plugins. The section is written only by `scripts/notes.py`, so its format stays parseable.

Relations encode their direction, so there is no separate parent/child field:

| Relation | From → to | Inverse (shown by `notes.py show`) |
|---|---|---|
| `part_of` | experiment, decision, hypothesis → project | `has_part` |
| `tests` | experiment → hypothesis | `tested_by` |
| `supports` | experiment → hypothesis | `supported_by` |
| `contradicts` | experiment → hypothesis | `contradicted_by` |
| `depends_on` | experiment → experiment, decision | `needed_by` |
| `motivated_by` | any → any | `motivates` |
| `supersedes` | experiment → experiment, decision → decision | `superseded_by` |

`tests` is for an experiment that is still running, or whose result bears on the hypothesis without settling it. Once it does settle it, replace `tests` with `supports` or `contradicts` before marking the experiment `done`.

Links are written on the **newer** note only, pointing to older notes. Inverses are never written into notes. This keeps the record append-only: finishing an experiment or making a decision never requires editing an older note.

Inline `[[links]]` in prose are allowed and checked, but carry no relation type.

## Evidence

`run` must use an immutable reference in the form:

```text
repository@commit:path
```

The referenced script should be a single self-contained bash script that contains (or points to, via committed paths) all config and parameters, so that it alone is enough to rerun the experiment.

`figures` use the same `repository@commit:path` form, or an absolute path on the cluster. Image and PDF files are blocked from this repository by `.gitignore` and by `check`.

Data lives on the shared cluster and is not version-controlled. To make it as stable as practical without new infrastructure:

- The run script writes a `MANIFEST.txt` into its output directory, listing the commit hash, the command, and each output file with its size and modification time.
- After a run, the output directory is made read-only (`chmod -R a-w`).
- If results were lost or moved, record that explicitly in `data`, e.g. `LOST 2026-10-14: results/highres_innovation/`.

## Rules

- Never rewrite a conclusion or decision. Once a note is `done`, a new note of the same type `supersedes` it.
- Every experiment and decision is `part_of` at least one project, and every finished experiment has a written conclusion.
- Evidence always cites a commit hash, never a branch.
- Use only the defined types, statuses, outcomes and relations.
- Use filename-based Obsidian links between notes, e.g. `[[high-res-innovation-diagnostic]]`. An `id` never changes after creation.
- Write links only on the newer note.
- The repository is text only.
- Create and modify notes through `scripts/notes.py`. The exception is a project page's prose, which may be edited directly.

## Tooling

`scripts/notes.py` (Python 3.7+, standard library only):

| Command | Does |
|---|---|
| `new TYPE TITLE [--link REL:TARGET[:NOTE]] [--body FILE] ...` | Creates a note. |
| `link ID REL TARGET [--note TEXT]` / `unlink ID REL TARGET` | Adds or removes a link on an editable note. |
| `set ID [--run ...] [--add-data ...] [--add-figure ...] [--body FILE] ...` | Changes fields or prose of an editable note. |
| `done ID [--outcome X]` | Freezes an experiment (outcome required) or a decision. |
| `show ID` | Prints a note with its incoming links. |
| `report` | Lists open experiments and decisions, uncited experiments and untested hypotheses. |
| `check` | Validates everything; exits 1 on any error. |

Besides the checks in [Nothing gets lost](#nothing-gets-lost), `check` enforces:

- `id` matches the filename, and the note is in the folder for its type;
- only `.md` files in `tree/` and `ideas/`;
- fields, types, statuses, outcomes and relations use allowed values, and relations connect the right types;
- `run` and `figures` are immutable references;
- every link target exists;
- `part_of`, `depends_on`, `motivated_by` and `supersedes` contain no cycles;
- experiments and decisions that were `done` at `HEAD` are unchanged;
- a done decision has a non-empty `## Decision`.

`scripts/hooks/pre-commit` runs `check`. Enable it with `git config core.hooksPath scripts/hooks`.
