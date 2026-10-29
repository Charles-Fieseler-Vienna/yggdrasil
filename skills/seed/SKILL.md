---
name: seed
description: Start or extend a project's ygg tree from the main tree, copying a main-tree question (or claim) with everything already under it, then expanding it into concrete sub-questions and planned runs. Use when the user wants to start working on a question from the main tree in a project repository, set up a project's tree, or break a question down into tasks.
---

# Seeding a project tree from the main tree

Work flows both ways between the main tree (compressed, cross-project) and a project's tree (detailed): a
project starts from main-tree questions (seeding), and its results go back up at the end of a phase
(compression, in the `ygg:tree` skill). Seeding copies notes rather than linking them, since a tree is a
self-contained vault; each copy records its `origin` (`repository@commit:nodeInstanceId`), which
`ygg compress` later uses to map the project's results back onto the original notes.

## 1. Settle the scope with the user

- **Which notes**: a main-tree Question (or Claim) to start from, by name; often one just made with
  `ygg:brainstorm`. Several are fine.
- **Which project tree**: usually `research/tree` in the project's repository. If it does not exist yet:
  `ygg init research/tree --project "<project title>"` in the repository, which also makes the notebook.
- **How much to bring**: by default the note and everything under it (follow-up questions, claims, their
  evidence and its sources and datasets). `--depth N` brings fewer steps down; done results under it come
  along as frozen context, which is usually what is wanted.

## 2. Seed

```bash
cd PROJECT/research/tree
ygg seed "QUE - ..." --dry-run   # show the user
ygg seed "QUE - ..."
```

`ygg seed` copies from the user's main tree (`ygg main` prints it); if none is set, ask the user which
tree it is and set it with `ygg main PATH`, or pass `--from TREE` to seed from another tree.
The main tree must be committed (the copies cite its commit). Seeding again later reuses what is already
here (and any paper Source with the same Zotero key or DOI), so it can pull in new main-tree notes. Links in
copied bodies to notes that were not copied become plain text. `ygg seed` appends a `seed` entry to the
notebook.

## 3. Expand into concrete work

The copied open questions are usually too broad to act on. Read them (`ygg show`) with the project's code and
data in mind, then propose, as an indented list:

```
QUE - <seeded question>
  QUE - <sub-question one analysis can answer>        follows from it
    EVD - <planned run or analysis>      open, high   informs the sub-question
    EVD - <next run>                     open         blocked by the first
  QUE - <another sub-question>
```

- **Sub-questions** follow from the seeded question and are narrow enough that one analysis or run group
  answers them. One idea per title, in the user's words.
- **Planned runs** are open Evidence notes informing a sub-question, with `## Purpose` (what it decides) and
  `## Method` (what to run, on which Dataset, and what result would answer it) filled in, and Results,
  Conclusion and Caveats left for later. They are the tasks; `ygg report` and the web app's Not done filter
  list them. When one is launched, log it with `ygg log ... --pid N --for "EVD - ..."`.
- **Order** with `blocked-by` where one needs another's result; `--priority high` on the one to three to do
  first.
- Seeded done claims are context: build on them with follow-up questions; never edit them.

Write what the user approves with `ygg` (bodies in scratch files), then `ygg check`, and log the plan:
`ygg log --tag decision "Plan for [[QUE - ...]]: ..."`.

## 4. In the main tree

Leave the main tree alone unless the user wants it to show the work is under way; then, there,
`ygg set "QUE - ..." --status in-progress` (and commit if asked). Results come back through `ygg compress`
at the end of the phase. Commit the project tree when the user asks.
