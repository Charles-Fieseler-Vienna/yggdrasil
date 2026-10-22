"""PostToolUse hook of the ygg plugin, after Bash calls: in a repository holding a ygg tree, nudge
Claude to keep the lab notebook when a command commits or launches a run. Prints nothing otherwise."""
import json
import os
import re
import sys
import time
from pathlib import Path

from session_start import find_trees  # same folder; hooks run with it on sys.path[0]

LAUNCH_RE = re.compile(r"\b(nohup|sbatch|srun|qsub|setsid)\b|\bscreen\s+-d|\btmux\s+new(-session)?\b.*\s-d\b"
                       r"|(?<!&)&\s*(disown\s*)?$", re.M)
COMMIT_RE = re.compile(r"\bgit\b[^|;&\n]*\bcommit\b")
YGG_RE = re.compile(r"(^|[;&|(]\s*|\s)(\S*/)?ygg\s")  # a ygg command anywhere: it is the logging itself
# A background command that only waits for something else (a loop on pgrep, sleep, tail -f) is not a run.
WAIT_RE = re.compile(r"\b(until|while)\b[^\n]*\b(sleep|pgrep|kill\s+-0|ps)\b|\btail\s+-[fF]|^\s*sleep\b")
QUOTED_RE = re.compile(r"'[^']*'|\"(\\.|[^\"\\])*\"|<<-?\s*'?(?P<tag>\w+)'?\n.*?\n\s*(?P=tag)\n?", re.S)
QUIET_MINUTES = 20


def nudge(event):
    inp = event.get("tool_input") or {}
    cmd = str(inp.get("command") or "")
    if YGG_RE.search(cmd):
        return None
    bare = QUOTED_RE.sub("''", cmd)  # what quotes and heredocs say ("detach with setsid") is not a command
    launched = (bool(inp.get("run_in_background")) and not WAIT_RE.search(bare)) or bool(LAUNCH_RE.search(bare))
    committed = bool(COMMIT_RE.search(bare))
    if not (launched or committed):
        return None
    trees = find_trees(Path(event.get("cwd") or os.getcwd()).resolve())
    if not trees:
        return None
    if launched:
        return ("This command looks like it started a run, in a repository with a ygg tree. If it is a run, log "
                "it now: `ygg log \"<what and why>\" --pid <pid> --log <path>` (repeat --pid and --log for a "
                "sweep; --job <id> for a cluster job; --for NOTE if a node for it exists). The PID is `$!` right "
                "after a `&` (`pgrep -f` also lists your own shell). It prints a run id: cite it wherever the "
                "result is recorded. "
                "To wait, run `ygg watch` in the background rather than a loop of your own: it returns when logged "
                "runs end, with the end of their logs, and reports failures on the way; "
                "`ygg drop ID -m why` gives a run up.")
    book = trees[0] / "NOTEBOOK.md"
    if book.exists() and time.time() - book.stat().st_mtime < QUIET_MINUTES * 60:
        return None
    return ("You committed in a repository with a ygg tree, and its notebook has no entry from the last %d "
            "minutes. If this commit settles a decision, a result or a dead end, record it with `ygg log` "
            "(or as a node); if not, carry on." % QUIET_MINUTES)


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    msg = nudge(event)
    if msg:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


if __name__ == "__main__":
    main()
