# CLAUDE.md

This repo is a cross-project research record in discourse-graph form: Questions, Claims, Evidence, Sources and Datasets in `tree/`, typed relations in `relations.json`, and project notes in `ideas/`. It holds only **compressed** nodes, the generalizable results and dead ends of each project. Each project keeps its detailed tree in its own repository in the same format. You maintain it on the user's behalf. `DESIGN.md` is the full specification; this file is how to work in it.

## The one rule

**Create and modify nodes and relations only with `scripts/ygg`.** Never write or edit files in `tree/`, `relations.json`, `ygg.json`, `templates/` or `.obsidian/` with Write, Edit, sed, heredocs or any other tool.

The one exception: the prose of a **project** note in `ideas/` (Summary, Findings, and any other narrative sections) may be edited directly with Edit. Change its frontmatter (`roots`) with `ygg set`.

To write a node's body, put the Markdown sections in a temporary file in your scratchpad and pass it with `--body FILE` (or `--body -` with stdin).

This repo is text only. Never add figures, PDFs or data. Reference them as `repository@commit:path` or an absolute cluster path.

The same rules apply in a project's own tree (e.g. `Cosyne_2027/research/tree/`); run `ygg` there, or pass `--vault PATH`.

## Before writing anything

1. Run `scripts/ygg report` for work in progress, open nodes, unanswered questions and orphans.
2. Read the relevant project notes in `ideas/`.
3. Use `ygg show NOTE` to read a note with its relations, or a project with its members.
4. Reuse existing nodes; relate to them rather than restating them.

## Common workflows

Notes are named by filename (`"CLM - Head bending is continuously driven"`), by the content after the prefix, or by any unique part of the filename. Titles cannot contain `: # ^ [ ] | \ / * ? " < >`.

**A question, then evidence, then a claim.**
```bash
ygg new question "Is the head wave driven at the head" --body q.md --link "follows-from:QUE - Parent question"
ygg new evidence "Head innovations travel down the body" --body evd.md \
  --link "derived-from:@Cosyne_2027 research tree" --link "derived-from:DATA - 36-animal cohort" \
  --link "informs:Is the head wave driven" --confidence medium
ygg done "Head innovations travel" --outcome succeeded
ygg new claim "Head bending is continuously driven" --body clm.md \
  --link "addresses:Is the head wave driven" --link-from "supports:Head innovations travel" --confidence medium
```
`--link REL:NOTE` means *new note REL NOTE*; `--link-from REL:NOTE` means *NOTE REL new note*. Relations: `supports`, `opposes`, `informs`, `derived-from`, `addresses`, `follows-from`, `supersedes`, `blocked-by`. The allowed type pairs are in `DESIGN.md`.

**A run in a project tree.** Create a Source for the run with `--run repository@commit:path` and the Evidence derived from it when the run is launched (`ygg set ... --status in-progress`); fill in the Evidence body and `ygg done` it when results are in. `run` must use a real commit hash (`git -C <repo> rev-parse --short HEAD`), never a branch. If the run used uncommitted code, tell the user rather than citing a commit that doesn't match.

**Compressing a project into this repo.** With the user, once the project's tree (or its old `TREE.md`) is committed:
```bash
ygg compress ~/Current_work/repos/Cosyne_2027/research/tree      # prints the outline, records the Source
```
Then write the compressed nodes with `ygg new`: about one Question per figure, one Claim per one to three panels, each Claim with its own Evidence derived from the tree Source and the Dataset. Keep generalizable results, dead ends and open questions; leave narrow methods details in the project tree. Add the root nodes with `ygg set PROJECT --add-root NOTE`.

**Changing a conclusion.** Never edit a `done` node. Create a new node of the same type with `--link supersedes:OLD`, saying what changed and why, then update the project's Findings.

**Finishing up.**
```bash
ygg check
```
Commit only when the user asks, or when they have asked you to maintain the repo as part of a workflow.

## Writing nodes

- **One idea per title.** No semicolons, sub-claims, guesses at causes or figure references; those go in the body.
- **A Question stays a Question.** When evidence answers it, add a Claim that `addresses` it. Never change a node's type.
- **Every Claim needs supporting Evidence**, and Claims and Evidence carry `confidence` (`low`, `medium`, `high`; `refuted` for Claims).
- **Conclusion is the important part of Evidence.** One to three sentences, readable on their own: what the result means, with effect size, n (animals, recordings), and which Dataset or subset.
- **Caveats are required** on Evidence: missing runs, data limits, anything that bounds the result, even if "none known".
- **Failed and ambiguous results are worth recording.** Say what would make them worth retrying.
- **Findings on project notes** are short claims citing Claim nodes, e.g. `- The head wave is driven at the head ([[CLM - Head bending is continuously driven]]).`
- **Use the user's words** for concepts that already have names in their project documents. Don't invent new terminology.
- **Cite papers** as Sources with `--citekey <key>`. The user's Zotero library is available through the Zotero tools if a key needs to be looked up.
- **Backfilling** old results: pass `--created` with the original date and `--legacy-ref` with where it came from (e.g. `"TREE 1.12"`).
