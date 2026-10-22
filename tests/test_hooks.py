import json
import os
import subprocess
import sys
import time

from conftest import ROOT, make_repo, run

HOOKS = ROOT / "hooks"


def hook(name, event):
    p = subprocess.run([sys.executable, str(HOOKS / name)], input=json.dumps(event), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True, env=dict(os.environ, CLAUDE_PLUGIN_ROOT=str(ROOT)))
    assert p.returncode == 0, p.stderr
    return p.stdout


def test_hooks_json_points_at_real_files():
    config = json.loads((HOOKS / "hooks.json").read_text())["hooks"]
    for event in config.values():
        for group in event:
            for h in group["hooks"]:
                path = h["command"].split('"/')[-1].replace('"', "")
                assert (ROOT / path).exists(), path


def test_session_start_silent_without_a_tree(tmp_path):
    assert hook("session_start.py", {"cwd": str(tmp_path)}) == ""
    make_repo(tmp_path / "proj", "research/tree")  # below, but tmp_path is no repository (like ~)
    assert hook("session_start.py", {"cwd": str(tmp_path)}) == ""


def test_session_start_finds_a_project_tree(tmp_path):
    root = make_repo(tmp_path / "proj", "research/tree")
    run("--vault", root, "log", "where we are", "--handoff")
    run("--vault", root, "log", "init is running", "--pid", "1", "--log", "fit.log")
    out = hook("session_start.py", {"cwd": str(tmp_path / "proj")})
    assert "load the ygg:tree skill" in out and "`research/tree`" in out
    assert "ygg:handoff" in out and "ygg:brainstorm" in out and "ygg:seed" in out
    assert "where we are" in out and "1 notebook entry since" in out
    assert "Runs since the last handoff or still running: 1 running." in out and "`ygg runs`" in out


def test_session_start_flags_a_decision_left_in_prose(tmp_path):
    root = make_repo(tmp_path / "proj")
    run("--vault", root, "log", "--ask", "Rerun on the new export?")
    run("--vault", root, "log", "--handoff", "--body", "-",
        stdin="Next\n- a261022-1 still waits.\n- Decide which null is fair (user decision).\n")
    out = hook("session_start.py", {"cwd": str(root)})
    assert "leaves a decision to the user in prose ('- Decide which null is fair (user decision).')" in out
    run("--vault", root, "log", "--handoff", "--body", "-", stdin="Next\n- The null waits on a261022-2 (user decision).\n")
    assert "leaves a decision" not in hook("session_start.py", {"cwd": str(root)})


def test_session_start_reports_format(tmp_path):
    root = make_repo(tmp_path / "proj")
    (root / "ygg.json").write_text(json.dumps({"spec_version": 0}))
    out = hook("session_start.py", {"cwd": str(root)})
    assert "run `ygg init` in it to upgrade" in out


def nudge(cwd, command, background=False):
    out = hook("post_bash.py", {"cwd": str(cwd), "tool_name": "Bash",
                                "tool_input": {"command": command, "run_in_background": background}})
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out.strip() else None


def test_post_bash(tmp_path):
    repo = tmp_path / "proj"
    root = make_repo(repo, "research/tree")
    book = root / "NOTEBOOK.md"
    old = time.time() - 3600
    os.utime(book, (old, old))
    assert "started a run" in nudge(repo, "nohup python fit.py > fit.log 2>&1 &")
    assert "started a run" in nudge(repo, "sbatch run.sh")
    assert "started a run" in nudge(repo, "python fit.py", background=True)
    assert "You committed" in nudge(repo, "git add -A && git commit -m 'x'")
    assert nudge(repo, "ls && echo done") is None
    assert nudge(repo, "ygg log 'x' && git commit -m x") is None
    assert nudge(repo, "cd research/tree && ygg log \"budget 1 h, detached with setsid &\"") is None
    assert nudge(repo, "git commit -m 'run it with nohup later'") is not None  # a commit, not a launch
    assert "started a run" not in nudge(repo, "git commit -m 'run it with nohup later'")
    assert nudge(repo, "until ! pgrep -f fit.py >/dev/null; do sleep 5; done; tail -5 fit.log",
                 background=True) is None
    assert nudge(repo, "tail -f fit.log", background=True) is None
    os.utime(book, None)
    assert nudge(repo, "git commit -m x") is None  # the notebook was just written
    assert "started a run" in nudge(repo, "nohup python fit.py &")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    assert nudge(elsewhere, "sbatch run.sh") is None
    # analysis scripts outside the repository
    assert "/tmp/x/angles.py" in nudge(repo, ".venv/bin/python /tmp/x/angles.py results/a")
    assert "/tmp/x/scan.py" in nudge(repo, "mkdir -p /tmp/x && cat > /tmp/x/scan.py <<'EOF'\nimport numpy\nEOF")
    assert "outside the repository" in nudge(repo, "python3 -u /tmp/fit.py && ygg log 'fit done'")
    assert nudge(repo, "python scripts/fit.py") is None
    assert nudge(repo, "python %s/scripts/fit.py" % repo) is None
    assert nudge(repo, "cat > /tmp/src.md <<'E'\nrun python /tmp/a.py\nE") is None  # a note body, a heredoc's text
    assert nudge(elsewhere, "python /tmp/fit.py") is None


def test_session_start_lists_open_issues_and_todos(tmp_path):
    root = make_repo(tmp_path / "proj")
    run("--vault", root, "log", "Bad frames in two recordings.", "--issue", "--todo", "rerun the fits")
    out = hook("session_start.py", {"cwd": str(root)})
    assert "Open issue i" in out and "Bad frames in two recordings." in out
    assert "1 open to-do in the notebook" in out
    run("--vault", root, "log", "--ask", "Drop the bad recordings?")
    out = hook("session_start.py", {"cwd": str(root)})
    assert "Waiting on the user (don't start what they block; `ygg asks`):\n  - a" in out
    assert "Drop the bad recordings?" in out and "1 open to-do" in out


def test_session_start_mentions_uncommitted_tree_changes(tmp_path):
    root = make_repo(tmp_path / "proj", "research/tree")
    out = hook("session_start.py", {"cwd": str(tmp_path / "proj")})
    assert "Uncommitted" not in out
    run("--vault", root, "new", "question", "Half done")
    run("--vault", root, "log", "cut off here")
    out = hook("session_start.py", {"cwd": str(tmp_path / "proj")})
    assert "Uncommitted in the tree: 1 note, NOTEBOOK.md" in out


def guard(cwd, command, **event):
    out = hook("pre_bash.py", dict(event, cwd=str(cwd), tool_name="Bash", tool_input={"command": command}))
    return json.loads(out)["hookSpecificOutput"] if out.strip() else None


def test_pre_bash_stops_self_matching_wait_loops(tmp_path):
    repo = tmp_path / "proj"
    make_repo(repo, "research/tree")
    out = guard(repo, 'until ! pgrep -f "n-matched" >/dev/null; do sleep 10; done; tail run.log')
    assert out["permissionDecision"] == "deny"
    assert "ygg watch" in out["permissionDecisionReason"] and "'[n]-matched'" in out["permissionDecisionReason"]
    assert guard(repo, "while pgrep -af 'metric isotropic' >/dev/null; do sleep 5; done")
    assert guard(repo, "for i in $(seq 1 16); do pgrep -f fit_lagged.py >/dev/null || break; sleep 25; done")
    assert guard(repo, "for f in *.py; do echo $f; done") is None
    # a bracket class, a loop on kill -0, or a one-off pgrep are fine; so is any loop outside a tree
    assert guard(repo, "until ! pgrep -f '[n]-matched' >/dev/null; do sleep 10; done") is None
    assert guard(repo, "while kill -0 123; do sleep 10; done") is None
    assert guard(repo, "pgrep -af n-matched | grep -v bash") is None
    (tmp_path / "elsewhere").mkdir()
    assert guard(tmp_path / "elsewhere", 'until ! pgrep -f "n-matched"; do sleep 10; done') is None


def test_pre_bash_caps_subagent_confidence(tmp_path):
    repo = tmp_path / "proj"
    make_repo(repo, "research/tree")
    sub = {"agent_id": "a1b2", "agent_type": "general-purpose"}
    cmd = 'cd research/tree && ygg new evidence "Fit wins" --body e.md --link "informs:Q" --confidence high'
    out = guard(repo, cmd, **sub)
    assert out["permissionDecision"] == "deny" and "--confidence medium" in out["permissionDecisionReason"]
    assert guard(repo, 'ygg set "CLM - X" --confidence refuted', **sub)
    assert guard(repo, cmd.replace("high", "medium"), **sub) is None
    assert guard(repo, cmd) is None  # the main session may
    assert guard(repo, "grep -- '--confidence high' notes.md && ygg show X", **sub) is None
    (tmp_path / "elsewhere").mkdir()
    assert guard(tmp_path / "elsewhere", cmd, **sub) is None

