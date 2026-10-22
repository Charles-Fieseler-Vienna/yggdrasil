---
name: brainstorm
description: Interview the user to grow a ygg research tree (usually the main tree) with new questions, connections across projects and papers, or to sketch a new project. Use when the user wants to brainstorm, think about what to work on next, explore an idea, connect projects, or start a project.
---

# Brainstorming in a ygg tree

A conversation that ends in new notes: questions, links between existing notes (especially across
projects), papers, and sometimes a new project. The user talks; you propose notes; they approve; you write
them with `ygg`. Follow the `ygg:tree` skill (all writes through `ygg`, one idea per title, the user's own
words for named concepts).

## 1. Get oriented, quietly

- **Which tree**: the one the session is in. In the middle of a project, brainstorming is often a break
  from the runs, in the project's own tree, and everything from it stays there, even ideas that belong
  elsewhere; never write to the main tree or another tree from a project brainstorm. Moving notes out is
  compression's job, later.
- `ygg report`, the notebook's recent `brainstorm` entries (`grep -n "brainstorm" NOTEBOOK.md`; ideas set
  aside before should not come back as new), and the project notes in `ideas/` that seem related.
- Search the tree for the topic: `grep -ril WORD tree/ ideas/`, then `ygg show NOTE` on the hits.
- Suggest the user open the web app (`ygg serve`, if it is not running: they start it, not you)
  to watch notes appear. Don't dump what you read back at them; use it in your questions.

## 2. Interview

Ask a few questions at a time, not a questionnaire. Useful directions:
- What prompted this? A result, a paper, a talk, a gap in a current project?
- What would an answer look like, and what would it change? (This separates a question from a topic.)
- Which existing questions, claims or results does it touch? Name candidates you found and ask.
- What would the first experiment or analysis be, and on which Dataset?
- What is known already: papers, results in other projects, dead ends?

Bring in what the tree knows: "Project X found Y ([[CLM - ...]]); does that bear on this?" Connections
between projects are the most valuable output, so look for them actively. Point out when an idea restates an
existing question instead of making a new one.

## 3. Propose, then write

After each topic, propose a short batch as a list the user can edit, e.g.:

```
New  QUE - Do contrastive latents recover posture dynamics      follows from QUE - What drives head curvature
New  QUE - Is the steering signal low-dimensional               (new root of project: ...)
Link CLM - Learned Koopman lifts do not improve posture forecasts  --informs?-->  (needs evidence; see below)
Paper  Laiz 2025 (Zotero 2Q9B3YAH) -> informs QUE - Do contrastive latents ...
```

Write only what they approve. For each:
- **Questions**: `ygg new question TITLE --body - --link "follows-from:..."`, or for a new root,
  `--link` nothing and then `ygg set PROJECT --add-root NOTE`. A question that connects to nothing yet may
  also stay loose, in no project: `ygg check` only warns, and it can be linked in later.
- **Out of scope**: in a project's tree, an idea that belongs elsewhere (the main tree, another project)
  is still written here, with `--out-of-scope`; compression moves it out later. Don't move it now. The body's `## Question` states it in full
  (with the `?`), `## Context` says why it matters and what prompted it, in the user's words.
- **Links between existing notes**: `ygg link`, only with relations the `ygg:tree` skill allows for the two types.
  A Claim does not inform a Question directly: a Claim `addresses` a Question, and a Question can
  `follows-from` a Claim. If the right link is "this result bears on that question", that is new Evidence.
- **Papers**: use the `ygg:paper` skill (Source linked to Zotero, plus Evidence for what it means).
- **Hunches and guesses** go in a question's Context, not in claims. A Claim needs supporting Evidence.
- New notes are `open` unless the user says otherwise; leave `priority` at normal unless they rank them.

## 4. A new project

In a project's tree, a new project is only out-of-scope questions for now; it is created in the main tree
after compression. In the main tree, when the ideas gather into something to pursue: create the root questions first, then
`ygg new project "Project title" --id short-slug --root "QUE - ..." --body -`, whose body (on stdin) has a short
`## Summary` (the aim, in the user's words) and an empty `## Findings`. Add later roots with
`ygg set short-slug --add-root NOTE`.
The project's detailed work later happens in its own repository's tree, started from these questions
with the `ygg:seed` skill; this note is its entry point here, and its results come back by compression.

## 5. Close

Record the session in the notebook, with what did not become notes: `ygg log --tag brainstorm --body FILE`,
saying in a few lines the ideas considered and set aside (and why), the open threads worth returning to, and
links to the notes made (`[[QUE - ...]]`). Then run `ygg check` and fix anything you caused, and summarise what
was added. Commit only when the user asks.
