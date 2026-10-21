# ygg

Tools for research trees in discourse-graph form: Questions, Claims, Evidence, Sources and Datasets kept as Obsidian notes, with typed relations, TaskNotes work status and a lab notebook. A project keeps a detailed tree in its own repository; a main tree holds the compressed, generalizable results of every project.

- `scripts/ygg`: the command line tool, the only writer of a tree (`ygg init`, `new`, `link`, `done`, `report`, `log`, `compress`, `check`, ...).
- `ygg serve`: a local web app for browsing and editing a tree.
- A Claude Code plugin: the `ygg` command on Claude's PATH, skills for working in a tree, adding and digesting papers, brainstorming and handing off, and a session hook that tells Claude where the work stands whenever a session starts in a tree.

```bash
claude plugin marketplace add ~/Current_work/repos/yggdrasil
claude plugin install ygg@yggdrasil
```

`DESIGN.md` is the full specification.
