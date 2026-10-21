---
name: digest
description: Digest a whole paper into a ygg tree, its questions, claims and evidence as nodes derived from the paper, optionally linked to the scripts in its code repository. Use when the user wants a paper (often their own) broken down into the graph to build on, rather than just cited; give it a paper and optionally its repository.
---

# Digesting a paper into a ygg tree

Where `ygg:paper` adds one paper as a Source and says what it means for a project, a digest breaks the paper
itself into the graph: its questions, the claims it makes and the evidence for each, all derived from the
paper. It is compression (see the `ygg:tree` skill) applied to a paper. The paper is the Source; there need
be no data or runs behind the Evidence. Use it for papers to build on, usually the user's own.

## 1. Settle the scope with the user

- **The paper**: a Zotero item, DOI, title or PDF path. **The code**, optionally: a local repository or a URL.
- **Which tree** (usually the main tree) and **where it hangs**: a new project for the paper (default for the
  user's own papers: `ygg new project "<short paper name>" --id ... --root ...`, with the paper's top
  questions as roots), or under an existing project's question.
- **Depth**: the main results only (three to six claims), or figure by figure (about one Question per figure,
  one Claim per one to three panels). For their own papers, ask which results they mean to build on, and go
  deeper there.

## 2. The paper Source

Follow `ygg:paper` steps 1 and 2: find the item in Zotero (add it by DOI if missing), reuse its Source if
`ygg show zotero:KEY` finds one, else create it `--status done` with `--zotero` and `--doi`.

## 3. Read the paper

Get the text with `zotero_get_item_fulltext`, or read the PDF (Read with `pages`). For a long paper, read it
in a subagent and have it return a structured outline: the questions asked; for each figure, what each panel
shows, with the numbers (effect sizes, n, statistics) and the datasets; the methods in brief; the limitations
the authors state; the open questions and future work in the Discussion.

## 4. Propose the outline

Show the user the nodes before writing them, as an indented list:

```
QUE - <question the paper asks>                        root of the project
  CLM - <claim, one idea>                    confidence  addresses the question
    EVD - <what the panels showed>           Fig. 2A-C   supports the claim
  QUE - <open question from the Discussion>              follows from the claim (open)
```

- **Claims** are what the paper establishes, in the user's (or the paper's) words, one idea per title, with
  no figure numbers in titles. `confidence` is how firmly the paper establishes it (`high` for a central,
  well-controlled result; `low` for a suggestive one). Negative results are claims too.
- **Evidence** per claim: `## Purpose`, `## Method` (brief, with the figure and panel references), `## Results`
  (the reported numbers), `## Conclusion` (one to three sentences with effect size and n), `## Caveats` (the
  stated limitations, and "as reported in the paper; not rerun"). Status `done`, outcome `succeeded` (or
  `failed` for a reported negative result), derived from the paper Source.
- **Datasets**: when the paper rests on a named dataset the user may reuse (their own recordings, a public
  dataset), a Dataset node (`--location`, `--n-animals`, `--n-recordings`) that the Evidence also derives from;
  reuse one if it exists.
- **Open questions** from the Discussion become open Questions that follow from the claims: these are the
  hooks for building on the paper.
- Reuse existing nodes instead of duplicating them, and link the digest to them: a claim that answers an
  existing question `addresses` it; an existing claim the paper supports gets new Evidence.

## 5. Link the code (when a repository is given)

The scripts are not results, but they say exactly how each figure was made, which is what building on it needs.
- Find the repository locally (or clone it into a scratch folder) and pick the commit matching the paper: a
  release or tag for it, else the last commit before publication. Use the full repository name and a real
  short hash (`git -C REPO rev-parse --short COMMIT`); if the match is uncertain, say so in Caveats.
- Find the script, notebook or config behind each figure (figure names in code, a README, a `figures/`
  folder, plotting functions). Ask the user when it is not clear; never guess a path.
- For each, a run Source: `ygg new source "<paper short name> <what it computes>" --run REPO@COMMIT:PATH
  --status done --link "derived-from:zotero:KEY" --body src.md`, whose Description says what it computes,
  which figure it makes, and that its outputs were not rerun here. Add data locations it documents with
  `--add-data`. The figure's Evidence then also derives from it (`ygg link "EVD - ..." derived-from "@..."`).
- One Source per script, shared by the Evidence of every figure it makes. Leave out helpers and utilities.

## 6. Write and finish

Write what the user approved with `ygg` (bodies in scratch files), questions and sources first, then evidence,
then claims. For a new project, write `## Summary` (the paper in two sentences, in the user's words) and
`## Findings` citing the Claim nodes. Run `ygg check`, then summarise: the nodes made or reused, the scripts
linked, and the open questions that are the natural next steps. Commit only when the user asks.
