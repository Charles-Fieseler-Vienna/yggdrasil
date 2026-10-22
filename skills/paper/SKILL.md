---
name: paper
description: Add a paper to a ygg research tree as a Source linked to Zotero, plus Evidence saying what it means for the project. Use when the user wants to add, cite or connect a paper (title, DOI, arXiv link, Zotero item) to a question or claim in the main tree or a project's tree.
---

# Adding a paper to a ygg tree

Zotero is the one home of the literature. In the tree a paper is a thin **Source** that points to its Zotero
item, and what it means for the project is a separate **Evidence** note derived from it. See `${CLAUDE_PLUGIN_ROOT}/DESIGN.md`,
section Papers. All writes go through `ygg` (in a project tree, `ygg --vault PATH` or run it there).

## 1. Identify the paper in Zotero

- Find it in the user's library: `zotero_search_items` by title or author, or `zotero_semantic_search` by
  topic. Get its **item key** (8 characters, e.g. `2Q9B3YAH`) and DOI with `zotero_get_item_metadata`.
- Not in the library: find the DOI (OpenAlex, Crossref or arXiv) and add it with `zotero_add_item` by DOI.
  If adding fails, record it in `zotero_pending_adds.md` as the `zotero-research` skill describes, and
  create the Source with the DOI only; add `--zotero` later with `ygg set`.
- Check the metadata against the DOI. Never invent a key or DOI, and don't fill in authors, year or venue
  from memory: if Zotero lacks them, take them from the DOI record (Crossref, OpenAlex), or leave them out
  and say so.
- For more than two or three papers at once, do the lookups in a subagent and have it return title,
  year, first author, item key and DOI for each, so the Zotero output stays out of the main context.

## 2. Reuse the Source if it exists

```bash
ygg show zotero:2Q9B3YAH        # or doi:10.48550/arXiv.2410.14673
```
If a Source is found, use it. Otherwise create one, titled with the paper's title (drop characters titles
cannot hold: `: # ^ [ ] | \ / * ? " < >`; a subtitle after a colon can usually go):
```bash
ygg new source "Self-supervised contrastive learning performs non-linear system identification" \
  --zotero 2Q9B3YAH --doi 10.48550/arXiv.2410.14673 --status done --body - <<'EOF'
## Description
Laiz et al. 2025, preprint. Theory and experiments for dynamics contrastive learning.
EOF
```
The body holds only `## Description` with one line: first author, year, venue, and what kind of paper it
is. The
abstract, reading notes and highlights stay in Zotero. `ygg new` refuses a second Source with the same key
or DOI, so a refusal means step 2 missed it: use the existing one.

## 3. Say what it means, as Evidence

Ask the user what the paper bears on if it is not clear: which question it informs, which claim it supports
or opposes. Then one Evidence note per point the project takes from it (usually one):
```bash
ygg new evidence "Contrastive learning recovers latent linear dynamics under nonlinear observation" \
  --link "derived-from:zotero:2Q9B3YAH" --link "informs:QUE - ..." --confidence medium --status done \
  --outcome succeeded --body - <<'EOF'
## Purpose
...
EOF
```
- The title is the finding in the paper that matters here, not the paper's title.
- The body follows the Evidence sections. **Conclusion**: what the paper shows that matters for this
  project, in one to three sentences, with its scale (data, n, setting). **Caveats**: how far it transfers
  here (species, data size, assumptions), and whether it was read in full or only the abstract.
- `confidence` is how much the project can lean on it here, not the paper's quality in general.
- To support or oppose a claim, link the Evidence `supports:CLM - ...` or `opposes:CLM - ...`.
- If the user is not sure yet what the paper is for, leave the Evidence `open` with what to check, or just
  relate the Source and ask; but a Source nothing derives from is not reachable from a project and fails
  `ygg check`, so it needs at least one Evidence note.

## 4. Finish

Run `ygg check`. Tell the user which Source and Evidence were created or reused, and give the
Zotero link (`zotero://select/library/items/KEY`). An open `ygg serve` page shows them at once. Commit only
when the user asks.
