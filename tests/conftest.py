"""Fixtures: throwaway trees in git repositories, and a runner for the CLI as users run it."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
YGG = ROOT / "scripts" / "ygg"
MAIN_TREE = Path.home() / "Current_work" / "repos" / "Yggdrasil-charlie"


def run(*args, cwd=None, ok=True, stdin=None):
    """Run `ygg ARGS` on plain python3; return (exit code, stdout + stderr)."""
    p = subprocess.run([sys.executable, str(YGG)] + [str(a) for a in args], cwd=cwd, input=stdin,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if ok is not None and (p.returncode == 0) != ok:
        raise AssertionError("ygg %s exited %d:\n%s" % (" ".join(map(str, args)), p.returncode, p.stdout))
    return p.returncode, p.stdout


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd)] + list(args), check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, universal_newlines=True).stdout


def commit(repo, msg="commit"):
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", msg, "--allow-empty")


def body(tmp_path, text, name="body.md"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


EVIDENCE = "## Purpose\n\np\n\n## Conclusion\n\nIt worked, R2 0.3, n=5.\n\n## Caveats\n\nnone known\n"
CLAIM = "## Claim\n\nc\n"


def make_repo(path, tree="."):
    """A git repository at `path` with a ygg tree at `path/tree` and one project, committed."""
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    root = path / tree
    run("init", root, "--project", "Test project")
    commit(path, "init")
    return root


@pytest.fixture
def tree(tmp_path):
    return make_repo(tmp_path / "repo")


@pytest.fixture
def ygg(tree):
    return lambda *args, ok=True, stdin=None: run("--vault", tree, *args, ok=ok, stdin=stdin, cwd=tree)


@pytest.fixture
def populated(tree, ygg, tmp_path):
    """Question <- evidence (derived from a run Source) -> claim addressing the question, all done."""
    ygg("new", "question", "Is the head wave driven at the head", "--status", "done",
        "--body", body(tmp_path, "## Question\n\nq\n"))
    ygg("set", "test-project", "--add-root", "Is the head wave driven")
    ygg("new", "source", "Head run", "--run", "repo@abc1234:run.sh", "--status", "done")
    ygg("new", "evidence", "Innovations travel down the body", "--body", body(tmp_path, EVIDENCE),
        "--link", "derived-from:Head run", "--link", "informs:Is the head wave driven", "--confidence", "medium")
    ygg("done", "Innovations travel", "--outcome", "succeeded")
    ygg("new", "claim", "Head bending is continuously driven", "--body", body(tmp_path, CLAIM),
        "--link", "addresses:Is the head wave driven", "--link-from", "supports:Innovations travel",
        "--confidence", "medium")
    ygg("done", "Head bending")
    commit(tree, "populate")
    return tree


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
