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


def find_trees(cwd):
    """Trees at or above cwd, else in its subfolders up to three levels down."""
    for d in [cwd] + list(cwd.parents):
        if (d / "ygg.json").is_file():
            return [d]
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
    running = [n.stem for n in nodes if n.status == "in-progress"]
    high = [n.stem for n in nodes if n.meta.get("priority") == "high" and n.status != "done"]
    for title, group in (("In progress", running), ("High priority", high)):
        if group:
            lines.append("  %s: %s" % (title, "; ".join("[[%s]]" % s for s in group[:12])
                                       + (" and %d more" % (len(group) - 12) if len(group) > 12 else "")))
    entries = ygg.notebook_entries(root)
    hand = [i for i, e in enumerate(entries) if "handoff" in e["tag"].lower()]
    if hand:
        e = entries[hand[-1]]
        text = e["text"] if len(e["text"]) <= HANDOFF_CHARS else e["text"][:HANDOFF_CHARS] + " […]"
        lines.append("  Last handoff (%s), in NOTEBOOK.md:\n\n%s\n" % (e["when"], text))
        later = len(entries) - hand[-1] - 1
        if later:
            lines.append("  %d notebook entr%s since that handoff; `ygg report --since handoff` lists them."
                         % (later, "y" if later == 1 else "ies"))
    elif entries:
        lines.append("  No handoff yet; the notebook has %d entries, the latest from %s."
                     % (len(entries), entries[-1]["when"]))
    found = ygg.run_states(vault)
    line = ygg.runs_summary(found)
    if line:
        lines.append("  " + line)
    lines += ["  " + x for x in ygg.needs_action(vault, found)]
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
           "`ygg log \"...\" --tag decision` (or dead-end, run, idea). When the user wraps up, offer the "
           "ygg:handoff skill; for papers use ygg:paper or ygg:digest.", ""]
    for root in trees:
        out += summary(ygg, root, cwd)
    print("\n".join(out))


if __name__ == "__main__":
    main()
