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


def test_session_start_finds_a_project_tree(tmp_path):
    root = make_repo(tmp_path / "proj", "research/tree")
    run("--vault", root, "log", "where we are", "--handoff")
    run("--vault", root, "log", "init is running", "--pid", "1", "--log", "fit.log")
    out = hook("session_start.py", {"cwd": str(tmp_path / "proj")})
    assert "load the ygg:tree skill" in out and "`research/tree`" in out
    assert "ygg:handoff" in out and "ygg:brainstorm" in out and "ygg:seed" in out
    assert "where we are" in out and "1 notebook entry since" in out
    assert "Runs since the last handoff or still running: 1 running." in out and "`ygg runs`" in out


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
