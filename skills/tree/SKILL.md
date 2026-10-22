---
name: tree
description: How to read and change a ygg research tree (a discourse graph of Questions, Claims, Evidence, Sources and Datasets kept as Obsidian notes). Load before creating, linking, finishing or superseding notes in any repository with a ygg.json, before compressing a project into the main tree, or when recording a run.
---

# Working in a ygg tree

A ygg tree is a folder with `ygg.json`: nodes in `tree/`, typed relations in `relations.json`, one note per
project in `ideas/`, and a lab notebook, `NOTEBOOK.md`. A **project tree** lives in its project's repository
at full detail; the user's **main tree** (Yggdrasil-charlie) holds only compressed nodes, the generalizable
results and dead ends of each project. The full specification is `${CLAUDE_PLUGIN_ROOT}/DESIGN.md`.

## The one rule

**Create and modify nodes and relations only with the `ygg` command** (on PATH through this plugin). Never
write or edit files in `tree/`, `relations.json`, `ygg.json`, `templates/` or `.obsidian/` with Write, Edit,
sed, heredocs or anything else. Run `ygg` inside the tree, or pass `--vault PATH`.

Exceptions: the prose of a **project** note in `ideas/` (Summary, Findings, other narrative sections) may be
edited with Edit; change its `roots` with `ygg set`. `NOTEBOOK.md` is appended to with `ygg log`, and its past
entries are never edited.

To write a node's body, put its Markdown sections in a scratch file and pass `--body FILE` (or `--body -`).

Trees are text only. Never add figures, PDFs or data; reference them as `repository@commit:path` or an
absolute cluster path.

## Before writing

1. `ygg report` (with `--project P`, `--since handoff`) for work in progress, priorities, open nodes, orphans.
2. Read the relevant project notes in `ideas/`; `ygg show NOTE` reads a note with its relations.
3. Reuse existing nodes; relate to them rather than restating them.

## Commands

Notes are named by filename (`"CLM - Head bending is continuously driven"`), the content after the prefix,
any unique part of the filename, or for papers `zotero:KEY` / `doi:DOI`. Titles cannot contain
`: # ^ [ ] | \ / * ? " < >`.

```bash
ygg new question "Is the head wave driven at the head" --body q.md --link "follows-from:QUE - Parent question"
ygg new evidence "Head innovations travel down the body" --body evd.md \
  --link "derived-from:@Cosyne_2027 research tree" --link "derived-from:DATA - 36-animal cohort" \
  --link "informs:Is the head wave driven" --confidence medium
ygg done "Head innovations travel" --outcome succeeded
ygg new claim "Head bending is continuously driven" --body clm.md \
  --link "addresses:Is the head wave driven" --link-from "supports:Head innovations travel" --confidence medium
ygg link SOURCE REL TARGET          # and ygg unlink
ygg set NOTE --status in-progress --priority high
ygg check                           # after every batch of changes
```
`--link REL:NOTE` means *new note REL NOTE*; `--link-from REL:NOTE` means *NOTE REL new note*. Allowed pairs:
Evidence `supports`/`opposes` Claim; Evidence `informs` Question; Claim `addresses` Question; Question
`follows-from` Question or Claim, Claim `follows-from` Claim; Evidence `derived-from` Source or Dataset,
Source `derived-from` Source or Dataset, Dataset `derived-from` Dataset; `supersedes` between notes of one
type; `blocked-by` among Questions, Claims and Evidence.

## Workflows

**Runs.** Log every run when it starts, in the notebook: `ygg log "what and why" --pid N --log PATH`
(repeat both for a sweep; `--job ID` for a cluster job; `--for NOTE` if it serves a note that exists). It
prints a run id. Most runs stay in the notebook: when one ends, note its result in a line citing the id
(`ygg log "r261022-41233: no gain over ridge"`), or give it up with `ygg drop ID -m "why"` (`--kill` stops
it). When a result matters, record it as a node: a Source with `--run repository@commit:path` and the
Evidence derived from it, citing the run ids in its Method. `run` uses a real commit (`git -C REPO rev-parse
--short HEAD`), never a branch; if the run used uncommitted code, tell the user rather than citing a commit
that doesn't match. `ygg runs` lists runs still going or not looked at; `ygg watch` (in the background)
returns when they end, reporting failures in their logs.

**Starting a project from the main tree.** `ygg seed NOTE --from MAIN_TREE` in the project's tree copies a
main-tree question (or claim) and everything under it, each copy recording its `origin`, and makes it a root;
the `ygg:seed` skill also expands it into concrete sub-questions and planned runs.

**Changing a conclusion.** Never edit a `done` node. Create a new node of the same type with
`--link supersedes:OLD`, saying what changed and why, then update the project's Findings.

**Compressing a project into the main tree** (with the user, once the project tree is committed): run
`ygg compress PATH/TO/project/tree` in the main tree; it prints the outline and records the tree as a Source.
Then write the compressed nodes: about one Question per figure, one Claim per one to three panels, each Claim
with its own Evidence derived from the tree Source and the Dataset. Keep generalizable results, dead ends and
open questions; leave narrow methods in the project tree. Add roots with `ygg set PROJECT --add-root NOTE`.
The outline's **Papers** list says which papers already have a Source in the main tree (derive from that one;
never make a second) and which lack a Zotero key or DOI. **Seeded from this tree** lists the notes copied
from the main tree with what the project added under them: write those against the original notes, not new
copies. On a second compression of the same tree, **Since the last compression** lists only the new and
changed notes, relations and notebook entries, and the outline marks them.

**The notebook.** While working, append decisions, dead ends and surprises as they happen:
`ygg log "..." --tag decision` (or `dead-end`, `run`, `idea`). At the end of a session use `ygg:handoff`.

**Papers** use `ygg:paper` (one paper as a Source plus what it means here) or `ygg:digest` (a whole paper
broken into questions, claims and evidence). **Brainstorming** uses `ygg:brainstorm`; starting a project from
the main tree uses `ygg:seed`.

**The web app.** `ygg serve` serves a local web app (port 8765) for browsing and editing. It never returns,
so don't run it yourself in the foreground; the user starts it, and an open page picks up CLI changes at once.

Commit only when the user asks, or has asked you to maintain the tree as part of a workflow.

## Writing nodes

- **One idea per title.** No semicolons, sub-claims, guesses at causes or figure references; those go in the body.
- **A Question stays a Question.** When evidence answers it, add a Claim that `addresses` it. Never change a node's type.
- **Every Claim needs supporting Evidence**, and Claims and Evidence carry `confidence` (`low`, `medium`, `high`; `refuted` for Claims).
- **Conclusion is the important part of Evidence.** One to three sentences, readable on their own: what the result means, with effect size, n (animals, recordings), and which Dataset or subset.
- **Caveats are required** on Evidence: missing runs, data limits, anything that bounds the result, even if "none known".
- **Failed and ambiguous results are worth recording.** Say what would make them worth retrying.
- **Findings on project notes** are short claims citing Claim nodes, e.g. `- The head wave is driven at the head ([[CLM - Head bending is continuously driven]]).`
- **Use the user's words** for concepts that already have names in their project documents. Don't invent new terminology.
- **Papers** are Sources titled with the paper's title, with `--zotero KEY` and `--doi`, created `--status done`; what a paper means for the project goes in Evidence derived from it. Never guess keys.
- **Backfilling** old results: pass `--created` with the original date and `--legacy-ref` with where it came from (e.g. `"TREE 1.12"`).
