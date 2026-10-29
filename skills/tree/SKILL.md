---
name: tree
description: How to read and change a ygg research tree (a discourse graph of Questions, Claims, Evidence, Sources and Datasets kept as Obsidian notes). Load before creating, linking, finishing or superseding notes in any repository with a ygg.json, or when recording a run.
---

# Working in a ygg tree

A ygg tree is a folder with `ygg.json`: nodes in `tree/`, typed relations in `relations.json`, one note per
project in `ideas/`, and a lab notebook, `NOTEBOOK.md`. A **project tree** lives in its project's repository
at full detail; the user's **main tree** (`ygg main` prints where it is) holds only compressed nodes, the generalizable
results and dead ends of each project. The full specification is `${CLAUDE_PLUGIN_ROOT}/DESIGN.md`.

## The one rule

**Create and modify nodes and relations only with the `ygg` command** (on PATH through this plugin). Never
write or edit files in `tree/`, `relations.json`, `ygg.json`, `templates/` or `.obsidian/` with Write, Edit,
sed, heredocs or anything else. Run `ygg` inside the tree, or pass `--vault PATH`.

Exceptions: the prose of a **project** note in `ideas/` (Summary, Findings, other narrative sections) may be
edited with Edit; change its `roots` with `ygg set`. `NOTEBOOK.md` is appended to with `ygg log`, and its past
entries are never edited.

To write a node's body, pass its Markdown sections on stdin, `ygg new ... --body - <<'EOF'` … `EOF` (the same
for `ygg set`, and `ygg log --body -`), rather than through a file such as `/tmp/evd.md`, which a session or
subagent running alongside may overwrite.

Trees are text only. Never add figures, PDFs or data; reference them as `repository@commit:path` or an
absolute cluster path.

## Before writing

1. `ygg report` (with `--project P`, `--since handoff`) for work in progress, priorities, open nodes, notes in no project, notes out of scope.
   Its list "What a session looks at first", also in the session briefing, is most important first; the user
   may have set that order (`ygg order`, theirs to change). Work down it unless the handoff says otherwise.
2. Read the relevant project notes in `ideas/`; `ygg show NOTE` reads a note with its relations.
3. Reuse existing nodes; relate to them rather than restating them.

## Commands

Notes are named by filename (`"CLM - Head bending is continuously driven"`), the content after the prefix,
any unique part of the filename, or for papers `zotero:KEY` / `doi:DOI`. Titles cannot contain
`: # ^ [ ] | \ / * ? " < >`.

```bash
ygg new question "Is the head wave driven at the head" --body - --link "follows-from:QUE - Parent question"
ygg new evidence "Head innovations travel down the body" --body - \
  --link "derived-from:@my-project research tree" --link "derived-from:DATA - 36-animal cohort" \
  --link "informs:Is the head wave driven" --confidence medium
ygg done "Head innovations travel" --outcome succeeded
ygg new claim "Head bending is continuously driven" --body - \
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
that doesn't match. So any script whose output feeds a result (a number in the notebook, an Evidence note)
goes in the repository (e.g. `scripts/`) and is committed before it is cited, never in `/tmp` or as a long
inline `python - <<EOF`; quick looks at data can stay inline. `ygg runs` lists runs still going or not looked at; `ygg watch` (in the background)
returns when they end, with the last lines of each log, reporting failures on the way. Wait with it rather than a loop of your own, and stop
any background wait you started before you finish (a leftover one keeps a headless session from ending).

**Starting a project from the main tree.** `ygg seed NOTE` in the project's tree copies a
main-tree question (or claim) and everything under it, each copy recording its `origin`, and makes it a root;
the `ygg:seed` skill also expands it into concrete sub-questions and planned runs.

**Changing a conclusion.** An open node is revised in place: `ygg set NOTE --body -` replaces its body
(keep it current when new evidence changes it). Never edit a `done` node: create a new node of the same type
with `--link supersedes:OLD`, saying what changed and why, then update the project's Findings. (A node marked
`done` by mistake since the last commit can still be reopened: `ygg set NOTE --status open`.)

**Compressing a project into the main tree** (with the user, once the project tree is committed) uses
`ygg:compress`.

**The notebook.** While working, append decisions, dead ends and surprises as they happen:
`ygg log "..." --tag decision` (or `dead-end`, `run`, `idea`). At the end of a session use `ygg:handoff`.
Small next steps are to-dos, task lines in an entry: `ygg log "..." --todo "check the H=50 fits"` (repeatable;
without text the entry is only the to-dos). Tick one when done with `ygg tick TEXT` (`-m` says what came of
it); `ygg report` lists the open ones. Never edit past entries otherwise. A next step that is an experiment
is a planned Evidence note, not a to-do.

**Keeping the tree current.** The notebook is the raw record; the notes are what the next session, the web
app and compression read. When a result settles something (a planned Evidence gets its answer, a Claim's
confidence should move, a decision held), put it in the notes in the same session, not only in an entry:
fill in and finish the Evidence, revise open Claims in place, add the Question it raises. Don't wait for a
handoff the user may not ask for; a long session may never get one, and a compaction loses the details.
`ygg log` says when findings are piling up unrecorded (eight entries newer than any change to the notes),
and so do the report and the session briefing.

**A problem in something results rest on** (a bug in code, bad recordings, a wrong preprocessing step): log
it at once as an issue, naming the notes it touches: `ygg log "what is wrong" --issue --affects "DATA - ..."`.
That includes a bug found in the code behind a recorded result: when an evaluation bug explains an
Evidence's numbers, the issue affects that Evidence, even if the tree has no node for the code; a `surprise`
entry alone leaves the old conclusion standing in the tree.
Don't invalidate everything below it. `ygg issues ID` lists every note resting on it; judge each with the
user: if the problem could change it, rerun and supersede it (a fixed Dataset supersedes the old one); if
not, write a notebook line naming the issue id and the note with the reason
(`ygg log "i261022-1: [[EVD - ...]] uses no Hilbert features"`). `ygg impact NOTE` shows what rests on any
note. When nothing is left to judge, `ygg resolve ID -m "how"`.

**A decision only the user can make** (scope, a definition, go or no-go on a result that sits on its bar):
make the judgment calls you can, and log them as decisions; ask the rest as a question, at once, naming the
notes it is about and the work it holds up: `ygg log "the context in two sentences" --ask "Adopt X?" --on
"CLM - ..." --blocks "EVD - ..."`. It waits on the user in the report, the session briefing and the web app,
where they answer it; don't restate it in handoffs or start the work it blocks. Answers since the last
handoff are listed first (`ygg asks --all` shows every one): act on them, citing the question id.

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
  A subagent writes at most `medium` (a hook refuses `high` and `refuted` from subagents) and gives its case
  in its report; the main session raises the confidence after checking the work. When you hand tree work to
  a subagent, tell it to load this skill and to change the tree only through `ygg`.
- **Conclusion is the important part of Evidence.** One to three sentences, readable on their own: what the result means, with effect size, n (animals, recordings), and which Dataset or subset.
- **Caveats are required** on Evidence: missing runs, data limits, anything that bounds the result, even if "none known".
- **Failed and ambiguous results are worth recording.** Say what would make them worth retrying.
- **Findings on project notes** are short claims citing Claim nodes, e.g. `- The head wave is driven at the head ([[CLM - Head bending is continuously driven]]).`
- **Use the user's words** for concepts that already have names in their project documents. Don't invent new terminology.
- **Papers** are Sources titled with the paper's title, with `--zotero KEY` and `--doi`, created `--status done`; what a paper means for the project goes in Evidence derived from it. Never guess keys.
- **Backfilling** old results: pass `--created` with the original date and `--legacy-ref` with where it came from (e.g. `"TREE 1.12"`).
