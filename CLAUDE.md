# CLAUDE.md

This repo is a cross-project research record. Experiments and decisions (`tree/`) are the frozen record; projects and hypotheses (`ideas/`) are the living synthesis. You maintain it on the user's behalf. `DESIGN.md` is the full specification; this file is how to work in it.

## The one rule

**Create and modify notes only with `python3 scripts/notes.py`.** Never write or edit files in `tree/` or `ideas/` with Write, Edit, sed, heredocs or any other tool.

The one exception: the prose of a **project** page (Summary, Findings, and any other narrative sections) may be edited directly with Edit. Leave its frontmatter, its `## Links` section and its Dataview blocks alone.

To write prose for a note, put the Markdown sections in a temporary file in your scratchpad and pass it with `--body FILE` (or `--body -` with stdin). Do not include `## Links` in the body; give links with `--link`.

This repo is text only. Never add figures, PDFs or data. Reference them as `repository@commit:path` or an absolute cluster path.

## Before writing anything

1. Run `python3 scripts/notes.py report` for open experiments and decisions, uncited experiments and untested hypotheses.
2. Read the relevant project pages in `ideas/`.
3. Use `notes.py show ID` to read a note together with its incoming links.
4. Reuse existing notes; link to them rather than restating them.

## Common workflows

**A new question.**
```bash
python3 scripts/notes.py new hypothesis "Is the head wave driven at the head?" \
  --body /path/to/body.md --link part_of:control-decomposition
```

**An experiment.** Create it when the run is launched; finish it when results are in.
```bash
python3 scripts/notes.py new experiment "High-res innovation diagnostic" \
  --body /path/to/purpose-and-method.md \
  --link tests:head-wave-hypothesis --link part_of:control-decomposition \
  --run Cosyne_2027@eabf5bd:scripts/run_highres_innovation.sh --run-start 2026-10-10T14:02

# when results are in:
python3 scripts/notes.py set high-res-innovation-diagnostic --run-end 2026-10-11T03:40 \
  --add-data /cluster/project/results/highres_innovation/ \
  --add-figure Cosyne_2027@1a2b3c4:paper/figures/fig2.pdf \
  --body /path/to/full-body.md        # Purpose, Method, Results, Conclusion, Caveats
python3 scripts/notes.py unlink high-res-innovation-diagnostic tests head-wave-hypothesis
python3 scripts/notes.py link high-res-innovation-diagnostic supports head-wave-hypothesis \
  --note "innovation peaks at head segments"
python3 scripts/notes.py done high-res-innovation-diagnostic --outcome succeeded
```
Then **update the `## Findings` of every project the experiment is part of**, citing it inline. `check` fails until you do. Add a new finding, or extend or revise an existing one; if the result changes an earlier finding, rewrite that finding and cite both experiments.

`run` must be `repository@commit:path` with a real commit hash (`git -C <repo> rev-parse --short HEAD`), never a branch. If the run used uncommitted code, tell the user rather than citing a commit that doesn't match.

**A decision.** Record choices that are bigger than a single result (a loss family, what goes into a model, which data to use), and decisions left to the user.
```bash
python3 scripts/notes.py new decision "Non-contrastive losses only" \
  --body /path/to/body.md \
  --link "motivated_by:negatives-mostly-false:most negatives share the behavioural state" \
  --link part_of:ssl-alignment
python3 scripts/notes.py done non-contrastive-losses-only   # once the user has made the call
```
The body has Context, Decision, Rationale and Alternatives considered. Leave a decision `open` while it is only proposed; never mark one `done` that the user hasn't agreed to. If it shapes the project, also link it inline in the project page's `## Decisions`. Small practical decisions don't need to be listed there.

**Changing a conclusion or decision.** Never edit a `done` note. Create a new note of the same type with `--link supersedes:OLD_ID` that says what changed and why, then update the project page.

**Finishing up.**
```bash
python3 scripts/notes.py check
```
Commit only when the user asks, or when they have asked you to maintain the repo as part of a workflow.

## Writing notes

- **One run, one experiment.** A parameter sweep launched as one job is one experiment. Separate follow-up runs are separate experiments, linked with `depends_on` or `motivated_by`.
- **Conclusion is the important part.** One to three sentences that a project's Findings can cite. Say what the result means, not only what the numbers are.
- **Numbers with their context:** effect size, n (animals, recordings), and whether it is the exploration subset or the full cohort.
- **Caveats are required**, even if they are "none known".
- **Failed and ambiguous results are worth recording.** They stop the same thing being redone. Say what would make it worth retrying.
- **Findings on project pages** are short claims, each citing the experiments it rests on, e.g. `- The head wave is driven at the head ([[high-res-innovation-diagnostic]]).`
- **Annotate links** with `:annotation` or `--note` when the reason isn't obvious from the titles.
- **Use the user's words** for concepts that already have names in their project documents. Don't invent new terminology.
- **Cite papers** with `--ref <citekey>`. The user's Zotero library is available through the Zotero tools if a key needs to be looked up.
- **Backfilling** old results: pass `--created` with the original date and `--legacy-ref` with where it came from (e.g. `"TREE 1.12"`).

## Choosing links

| If the new note… | use |
|---|---|
| belongs to a project | `part_of` → project |
| is an experiment addressing a hypothesis, not yet settled | `tests` → hypothesis |
| is an experiment that settles a hypothesis | `supports` / `contradicts` → hypothesis |
| uses another experiment's outputs or results, or follows from a decision | `depends_on` → experiment or decision |
| exists because of an earlier note | `motivated_by` |
| is a decision prompted by results | `motivated_by` → experiment |
| replaces an earlier `done` experiment or decision | `supersedes` → same type |

Always write the link on the new note, pointing to the older one.
