"""PreToolUse hook of the ygg plugin, before Bash calls: in a repository holding a ygg tree, stop a wait
loop that can never end, one polling `pgrep -f PATTERN` (the shell running the loop has PATTERN in its own
command line, so pgrep always finds it), and stop a subagent from setting a note's confidence above medium
(the main session raises it after review). Prints nothing otherwise."""
import json
import os
import re
import sys
from pathlib import Path

from session_start import find_trees  # same folder; hooks run with it on sys.path[0]

LOOP_RE = re.compile(r"\b(until|while)\b")
# pgrep or pkill -0 style polling with -f among its flags, then the pattern (quoted or bare)
# a ygg command (new, set...) giving --confidence high or refuted
STRONG_RE = re.compile(r"(^|[;&|(]\s*|\s)(\S*/)?ygg\s[^;&|\n]*--confidence[=\s]+['\"]?(?P<level>high|refuted)\b")
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


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    cmd = str((event.get("tool_input") or {}).get("command") or "")
    strong = STRONG_RE.search(cmd) if event.get("agent_id") else None  # agent_id: the call comes from a subagent
    pat = self_matching(cmd)
    if not (strong or pat) or not find_trees(Path(event.get("cwd") or os.getcwd()).resolve()):
        return
    if strong:
        return deny("A subagent records confidence at most `medium` in a ygg tree: run the command again with "
                    "`--confidence medium`, and say in your report why it could be %s. The main session, which "
                    "sees the whole tree, raises it after review (`ygg set NOTE --confidence %s`)."
                    % ((strong.group("level"),) * 2))
    reason = ("This loop would never end: `pgrep -f %s` also finds the shell running the loop, whose command "
              "line holds the pattern. To wait for logged runs, run `ygg watch` in the background: it returns "
              "when they end, with the end of their logs. To wait on one process, loop on `kill -0 PID`; to "
              "keep pgrep, open the pattern with a bracket class (`pgrep -f '[%s]%s'`)." % (pat, pat[:1], pat[1:]))
    deny(reason)


if __name__ == "__main__":
    main()
