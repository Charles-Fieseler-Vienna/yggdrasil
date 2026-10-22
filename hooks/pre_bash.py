"""PreToolUse hook of the ygg plugin, before Bash calls: in a repository holding a ygg tree, stop a wait
loop that can never end, one polling `pgrep -f PATTERN` (the shell running the loop has PATTERN in its own
command line, so pgrep always finds it). Prints nothing otherwise."""
import json
import os
import re
import sys
from pathlib import Path

from session_start import find_trees  # same folder; hooks run with it on sys.path[0]

LOOP_RE = re.compile(r"\b(until|while)\b")
# pgrep or pkill -0 style polling with -f among its flags, then the pattern (quoted or bare)
PGREP_F_RE = re.compile(r"\bpgrep((?:\s+-\w+)*?\s+-\w*f\w*)(?:\s+-\w+)*\s+(?P<pat>\"[^\"]*\"|'[^']*'|\S+)")


def self_matching(cmd):
    """The first pgrep -f pattern in a loop that the loop's own shell matches, or None. A pattern opening
    with a bracket class ("[n]-matched") does not match its own text, so it is fine."""
    if not LOOP_RE.search(cmd):
        return None
    for m in PGREP_F_RE.finditer(cmd):
        pat = m.group("pat").strip("'\"")
        if not pat.startswith("["):
            return pat
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    pat = self_matching(str((event.get("tool_input") or {}).get("command") or ""))
    if not pat or not find_trees(Path(event.get("cwd") or os.getcwd()).resolve()):
        return
    reason = ("This loop would never end: `pgrep -f %s` also finds the shell running the loop, whose command "
              "line holds the pattern. To wait for logged runs, run `ygg watch` in the background: it returns "
              "when they end, with the end of their logs. To wait on one process, loop on `kill -0 PID`; to "
              "keep pgrep, open the pattern with a bracket class (`pgrep -f '[%s]%s'`)." % (pat, pat[:1], pat[1:]))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


if __name__ == "__main__":
    main()
