"""SessionStart hook of the ygg plugin: if the session's repository holds a ygg tree, tell Claude how to
work in it and where the work stands (the last handoff, what is in progress or high priority).
Prints nothing anywhere else, so sessions in other repositories see no ygg rules at all."""
import json
import os
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

SKIP = {"node_modules", "venv", "__pycache__", "site-packages"}  # and hidden folders
HANDOFF_CHARS = 2500
AGENDA_CAP = 12


def find_trees(cwd):
    """Trees at or above cwd, else, inside a git repository, in its subfolders up to three levels down."""
    for d in [cwd] + list(cwd.parents):
        if (d / "ygg.json").is_file():
            return [d]
    if not any((d / ".git").exists() for d in [cwd] + list(cwd.parents)):
        return []  # e.g. a session in ~ should not announce a tree three folders down
    found = []
    for root, dirs, files in os.walk(cwd):
        depth = len(Path(root).relative_to(cwd).parts)
        if "ygg.json" in files:
            found.append(Path(root))
            dirs[:] = []
            continue
        dirs[:] = [] if depth >= 3 else [x for x in dirs if x not in SKIP and not x.startswith(".")]
    return sorted(found)[:3]


def load_ygg():
    plugin = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
    return SourceFileLoader("ygg", str(plugin / "scripts" / "ygg")).load_module()


def summary(ygg, root, cwd):
    where = os.path.relpath(root, cwd)
    lines = []
    mismatch = ygg.format_mismatch(ygg.tree_format(root))
    if mismatch:
        lines.append("- `%s`: %s." % (where, mismatch))
    try:
        vault = ygg.Vault(root)
    except Exception as e:  # a broken tree still gets the rules
        return ["- `%s`: could not be read (%s); run `ygg --vault %s check`." % (where, e, where)]
    nodes = sorted(vault.nodes.values(), key=lambda n: n.stem)
    lines.append("- `%s`: %d notes in %d project%s (%s)." % (
        where, len(nodes), len(vault.projects), "" if len(vault.projects) == 1 else "s",
        ", ".join(sorted(vault.projects)) or "none"))
    first = list(ygg.agenda(vault).items())
    if first:
        placed = ygg.agenda_order(root)
        mine = sum(1 for s, _ in first if s in placed["stems"]) if placed else 0
        order = ("the first %d in the order the user set on %s, then " % (mine, placed["when"]) if mine else "") + (
            "answered by the user, in progress, high priority, named in the last handoff; blocked ones last, unnumbered")
        lines.append("  What to look at first, most important first (%s):" % order)
        lines += ["  " + l for l in ygg.agenda_lines(first, AGENDA_CAP, " (`ygg report`)")]
    entries = ygg.notebook_entries(root)
    hand = [i for i, e in enumerate(entries) if "handoff" in e["tag"].lower()]
    if hand:
        e = entries[hand[-1]]
        text = e["text"] if len(e["text"]) <= HANDOFF_CHARS else e["text"][:HANDOFF_CHARS] + " […]"
        lines.append("  Last handoff (%s), in NOTEBOOK.md:\n\n%s\n" % (e["when"], text))
        prose = ygg.prose_decision(e["text"], root)
        if prose:
            lines.append("  That handoff leaves a decision to the user in prose (%r) with no question asked. Ask it "
                         "now, once, so it waits for them: `ygg log \"the context\" --ask \"...?\" --on NOTE "
                         "--blocks NOTE`." % prose[:120])
        later = len(entries) - hand[-1] - 1
        if later:
            lines.append("  %d notebook entr%s since that handoff; `ygg report --since handoff` lists them."
                         % (later, "y" if later == 1 else "ies"))
    elif entries:
        lines.append("  No handoff yet; the notebook has %d entries, the latest from %s."
                     % (len(entries), entries[-1]["when"]))
    dirty = ygg.uncommitted(root)
    if dirty:
        lines.append("  Uncommitted in the tree: %s. A session may have stopped before recording and committing "
                     "its work: check `git status` and the notebook's latest entries." % dirty)
    for title, group in (("Waiting on the user (don't start what they block; `ygg asks`)",
                          [q for q in ygg.all_asks(root) if not q["answer"]]),
                         ("Answered by the user since the last handoff: act on these",
                          ygg.asks_answered_since_handoff(root))):
        if group:
            lines.append("  %s:\n" % title + "\n".join("  " + l for q in group[:8] for l in ygg.describe_ask(q)))
    issues = [i for i in ygg.issue_states(vault) if not i["resolved"]]
    for i in issues[:5]:
        lines.append("  Open issue " + "\n  ".join(ygg.describe_issue(i))[2:])
    todos = [t for t in ygg.all_todos(root) if not t["done"]]
    if todos:
        lines.append("  %d open to-do%s in the notebook (`ygg report` lists them)." % (len(todos), "" if len(todos) == 1 else "s"))
    found = ygg.run_states(vault)
    line = ygg.runs_summary(found)
    if line:
        lines.append("  " + line)
    lines += ["  " + x for x in ygg.needs_action(vault, found)]
    distil = ygg.distil_reminder(vault)
    if distil:
        lines.append("  " + distil)
    return lines


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    cwd = Path(event.get("cwd") or os.getcwd()).resolve()
    trees = find_trees(cwd)
    if not trees:
        return
    ygg = load_ygg()
    out = ["This repository holds a ygg research tree (a discourse graph of Questions, Claims, Evidence, "
           "Sources and Datasets). Before creating or changing notes, load the ygg:tree skill; change notes "
           "and relations only with the `ygg` command, never by editing tree/, relations.json or ygg.json. "
           "Keep the tree's lab notebook: append decisions, dead ends and surprises as they happen with "
           "`ygg log \"...\" --tag decision` (or dead-end, idea), and log every run you launch with "
           "`ygg log ... --pid N --log PATH`. The notebook is the raw record, not the result: when a finding "
           "settles or overturns something the notes say, put it in the notes during the session (load ygg:tree "
           "first), and when it shows a recorded result was wrong, log an issue on that note (`ygg log \"...\" "
           "--issue --affects NOTE`). When the user wraps up, offer the ygg:handoff skill. When they "
           "step back to think about what to pursue, use ygg:brainstorm; ygg:seed starts a project's tree "
           "from questions in another tree, and ygg:compress brings a project's results back. For papers "
           "use ygg:paper or ygg:digest.", ""]
    main_root = ygg.main_tree()
    if main_root in trees:
        out.append("`%s` is the user's main tree: projects are seeded from it and compressed back into it."
                   % os.path.relpath(main_root, cwd))
    elif main_root and not (main_root / "ygg.json").exists():
        out.append("The user's main tree is set to `%s`, which is not a ygg tree any more. Before seeding or "
                   "compressing, ask the user where it is now and set it with `ygg main PATH`." % main_root)
    elif main_root:
        out.append("The user's main tree, which projects are seeded from and compressed into, is `%s`." % main_root)
    else:
        out.append("No main tree is set. Before seeding or compressing, ask the user which tree is their main "
                   "tree (or whether to make one) and set it with `ygg main PATH`.")
    for root in trees:
        out += summary(ygg, root, cwd)
    print("\n".join(out))


if __name__ == "__main__":
    main()
