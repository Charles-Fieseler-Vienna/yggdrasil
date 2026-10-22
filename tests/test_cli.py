import json
import os
import re
import shutil
import subprocess
import sys
import time

import pytest

from conftest import (CLAIM, EVIDENCE, MAIN_TREE, ROOT, body, commit, git, load_json, make_repo, run)


def test_version_matches_plugin():
    _, out = run("--version")
    version = re.search(r"ygg (\S+) \(tree format (\d+)\)", out)
    assert version, out
    assert load_json(ROOT / ".claude-plugin" / "plugin.json")["version"] == version.group(1)
    assert version.group(1) in (ROOT / "CHANGELOG.md").read_text()


def test_planned_evidence_is_not_a_gap(tree):
    sys.path.insert(0, str(ROOT / "scripts"))
    from importlib.machinery import SourceFileLoader
    y = SourceFileLoader("ygg_flags", str(ROOT / "scripts" / "ygg")).load_module()
    run("--vault", tree, "new", "question", "Does it hold")
    run("--vault", tree, "new", "evidence", "Pilot run", "--link", "informs:Does it hold", "--confidence", "low")
    flags = y.node_flags(y.Vault(tree))
    assert flags["EVD - Pilot run"] == "open" and flags["QUE - Does it hold"] == "open"


def test_vault_goes_before_or_after_the_command(tree):
    for argv in (("--vault", tree, "check"), ("check", "--vault", tree)):
        _, out = run(*argv)
        assert ", 0 errors" in out


def test_init_makes_a_valid_tree(tree, ygg):
    for name in ("ygg.json", "relations.json", "NOTEBOOK.md", "ideas/test-project.md", "templates/ygg-claim.md",
                 ".obsidian/plugins/discourse-graphs/data.json"):
        assert (tree / name).exists(), name
    _, out = ygg("check")
    assert "0 errors" in out


def test_question_evidence_claim(populated, ygg):
    _, out = ygg("check")
    assert "4 nodes, 1 projects, 4 relations, 0 errors" in out
    _, out = ygg("show", "Head bending")
    assert "is supported by [[EVD - Innovations travel down the body]]" in out
    assert "addresses [[QUE - Is the head wave driven at the head]]" in out
    _, out = ygg("show", "test-project")
    assert out.count("\n- ") == 4


def test_claim_needs_evidence(tree, ygg, tmp_path):
    ygg("new", "question", "Q one", "--body", body(tmp_path, "## Question\n\nq\n"))
    ygg("set", "test-project", "--add-root", "Q one")
    ygg("new", "claim", "Lonely claim", "--link", "addresses:Q one")
    code, out = ygg("check", ok=False)
    assert code == 1 and "needs at least one supporting evidence" in out


@pytest.mark.parametrize("title", ["Has: colon", "Has? mark", "a/b"])
def test_bad_titles_refused(ygg, title):
    code, out = ygg("new", "question", title, ok=False)
    assert "titles cannot contain" in out


def test_disallowed_relation_refused(populated, ygg):
    _, out = ygg("link", "Head bending", "informs", "Is the head wave", ok=False)
    assert "informs cannot go from a claim to a question" in out


def test_done_notes_are_frozen(populated, ygg):
    _, out = ygg("set", "Head bending", "--priority", "high", ok=False)
    assert "done and frozen" in out
    _, out = ygg("unlink", "Innovations travel", "supports", "Head bending", ok=False)
    assert "cannot be removed" in out
    path = populated / "tree" / "CLM - Head bending is continuously driven.md"
    path.write_text(path.read_text().replace("## Claim\n\nc", "## Claim\n\nchanged"))
    code, out = ygg("check", ok=False)
    assert "was done at HEAD and has been changed" in out


def test_supersede(populated, ygg, tmp_path):
    ygg("new", "claim", "Head bending is driven in bursts", "--body", body(tmp_path, CLAIM),
        "--link", "supersedes:Head bending is continuously", "--link-from", "supports:Innovations travel")
    _, out = ygg("check")
    assert "0 errors" in out


def test_papers(tree, ygg):
    ygg("new", "question", "Q paper")
    ygg("set", "test-project", "--add-root", "Q paper")
    ygg("new", "source", "A paper", "--zotero", "2q9b3yah", "--doi", "https://doi.org/10.1234/ABC", "--status", "done")
    meta = (tree / "tree" / "@A paper.md").read_text()
    assert "zotero: 2Q9B3YAH" in meta and "doi: 10.1234/ABC" in meta
    _, out = ygg("new", "source", "Same paper", "--doi", "10.1234/abc", ok=False)
    assert "already has doi" in out
    _, out = ygg("show", "zotero:2Q9B3YAH")
    assert "doi: 10.1234/ABC" in out


def test_notebook_and_report_since_handoff(populated, ygg):
    ygg("log", "before", "--tag", "idea")
    ygg("log", "where things stand", "--handoff")
    ygg("log", "after [[CLM - Head bending is continuously driven]]", "--tag", "decision")
    _, out = ygg("report", "--since", "handoff")
    entries = out.split("## Notebook entries")[1]
    assert "handoff: where things stand" in entries and "decision: after" in entries and "before" not in entries
    _, out = ygg("log", "a [[Missing note]]")
    assert "does not exist" in out
    _, out = ygg("check")
    assert "warning: NOTEBOOK.md: [[Missing note]] does not exist" in out


def log_run(ygg, text, *args):
    _, out = ygg("log", text, *args)
    return re.search(r"run id: (\S+)", out).group(1)


def test_runs_are_logged_and_looked_at(populated, ygg, tmp_path):
    ygg("new", "evidence", "Pending fit", "--link", "informs:Is the head wave")
    _, out = ygg("log", "x", "--log", "a.log", ok=False)
    assert "give its --pid" in out
    sleeper = subprocess.Popen(["sleep", "60"])
    try:
        ended = [subprocess.Popen(["true"]) for _ in range(3)]
        for e in ended:
            e.wait()
        (populated / "fit.log").write_text("epoch 1\n")
        quiet = populated / "quiet.log"
        quiet.write_text("x\n")
        os.utime(quiet, (time.time() - 5 * 3600,) * 2)
        old = log_run(ygg, "before the handoff", "--pid", str(ended[0].pid))
        ygg("log", "--handoff", "where we are")
        sweep = log_run(ygg, "lag sweep", "--pid", str(sleeper.pid), "--pid", str(ended[1].pid), "--log", "fit.log",
                        "--log", "~/surely-missing.out")
        fit = log_run(ygg, "fit", "--pid", str(ended[2].pid), "--for", "Pending fit")
        loose = log_run(ygg, "quick check", "--pid", str(ended[1].pid))
        stuck = log_run(ygg, "stuck one", "--pid", str(os.getpid()), "--log", "quiet.log")
        job = log_run(ygg, "on the cluster", "--job", "123456", "--log", "/scratch/slurm-123456.out")
        book = (populated / "NOTEBOOK.md").read_text()
        assert "run %s · pids %d, %d · host " % (sweep, sleeper.pid, ended[1].pid) in book
        assert "· logs fit.log, ~/surely-missing.out" in book and "· for [[EVD - Pending fit]]" in book
        assert job.startswith("r") and "-j123456" in job and "— run" in book

        _, out = ygg("report")
        assert "Runs since the last handoff or still running: 2 running, 2 ended, 1 cluster job." in out
        action = out.split("## Needs action (3)")[1]
        assert "%s ended" % fit in action and "[[EVD - Pending fit]] is not done" in action
        assert "%s ended" % loose in action and "nothing mentions it yet" in action
        assert "%s is running, but quiet.log was last written 5 h ago" % stuck in action
        assert old not in action  # before the handoff: left as notebook material

        ygg("log", "%s: nothing new" % loose)  # a line in the notebook is enough
        ygg("set", "Pending fit", "--body", body(tmp_path, EVIDENCE + "\nFrom run %s.\n" % fit))
        ygg("done", "Pending fit", "--outcome", "succeeded")
        _, out = ygg("report")
        assert "Needs action (1)" in out

        _, out = ygg("runs")
        assert sweep in out and job in out and fit not in out and old not in out
        assert "fit.log: last written just now" in out and "surely-missing.out: not on this machine" in out
        assert "cluster job, check it yourself" in out
        _, out = ygg("runs", "--all")
        assert old in out and fit in out
        _, out = ygg("runs", "Pending fit")
        assert fit in out and sweep not in out
        _, out = ygg("show", "Pending fit")
        assert "<!-- runs (generated) -->" in out and fit in out
    finally:
        sleeper.kill()


def test_drop(populated, ygg):
    ygg("new", "evidence", "Pending fit", "--link", "informs:Is the head wave")
    runner = subprocess.Popen(["sleep", "60"])
    try:
        done = subprocess.Popen(["true"])
        done.wait()
        fit = log_run(ygg, "fit", "--pid", str(done.pid), "--for", "Pending fit")
        sweep = log_run(ygg, "sweep", "--pid", str(runner.pid))
        _, out = ygg("report")
        assert "Needs action (1)" in out
        _, out = ygg("drop", fit, sweep, "-m", "Pivoted to the GRU model.")
        assert "still running: %s (use --kill to stop it)" % sweep in out
        _, out = ygg("report")
        assert "Needs action" not in out
        _, out = ygg("runs")
        assert "%s (" % sweep in out and "dropped, still running" in out and fit not in out
        _, out = ygg("watch")
        assert "Nothing to watch" in out
        ygg("drop", sweep, "--kill")
        runner.wait(5)
        assert "Stopped PID %d." % runner.pid in (populated / "NOTEBOOK.md").read_text()
        _, out = ygg("drop", "r000000-1", ok=False)
        assert "no run r000000-1" in out
    finally:
        runner.kill()


def test_watch(populated, ygg):
    _, out = ygg("watch")
    assert "Nothing to watch" in out
    ygg("new", "evidence", "Pending fit", "--link", "informs:Is the head wave")
    short, long_ = subprocess.Popen(["sleep", "2"]), subprocess.Popen(["sleep", "60"])
    log = populated / "fit.log"
    log.write_text("old Traceback (most recent call last) before the watch\n")
    try:
        fit = log_run(ygg, "fit", "--pid", str(short.pid), "--log", "fit.log", "--for", "Pending fit")
        other = log_run(ygg, "other", "--pid", str(long_.pid))
        watch = subprocess.Popen([sys.executable, str(ROOT / "scripts" / "ygg"), "--vault", str(populated), "watch",
                                  "--first", "--interval", "0.3"], stdout=subprocess.PIPE, universal_newlines=True)
        time.sleep(1)
        with log.open("a") as f:
            f.write("epoch 3\nRuntimeError: CUDA error: out of memory\n")
        out, _ = watch.communicate(timeout=20)
        lines = out.splitlines()
        assert lines[0].startswith("Watching %s, %s on " % (fit, other)) and "ends when the first ends" in lines[0]
        assert "%s: failure in fit.log: RuntimeError: CUDA error: out of memory" % fit in out
        assert "old Traceback" not in out
        assert "%s ended, for [[EVD - Pending fit]]." % fit in out
        assert "%s ended" % fit in lines[-1] and "is not done" in lines[-1]
        _, out = ygg("watch", "Pending fit")
        assert "Nothing to watch" in out
    finally:
        long_.kill()


def test_report_is_compact(tree, ygg):
    for i in range(12):
        ygg("new", "question", "Question %02d" % i)
        ygg("set", "test-project", "--add-root", "Question %02d" % i)
    _, out = ygg("report")
    assert "## In progress" not in out  # empty groups are left out
    open_ = out.split("## Open (12)")[1].split("##")[0]
    assert open_.count("\n- ") == 9 and "… and 4 more (`--all`)" in open_
    _, out = ygg("report", "--all")
    assert out.split("## Open (12)")[1].split("##")[0].count("\n- ") == 12
    _, out = ygg("report", "--project", "test-project")
    assert "[test-project]" not in out


def test_format_versions(tree, ygg):
    (tree / "ygg.json").write_text(json.dumps({"spec_version": 0}))
    code, out = ygg("check", ok=False)
    assert "run `ygg init` in it to upgrade" in out
    _, out = ygg("report")
    assert "warning: this tree is in format 0" in out
    (tree / "ygg.json").write_text(json.dumps({"spec_version": 99}))
    _, out = ygg("check", ok=False)
    assert "newer than this ygg" in out
    run("init", tree)
    _, out = ygg("check")
    assert "0 errors" in out


# --- Seeding and compression ---------------------------------------------------------

@pytest.fixture
def project(tmp_path):
    root = make_repo(tmp_path / "proj", "research/tree")
    return root


def seed(project, *args, ok=True):
    return run("--vault", project, "seed", *args, ok=ok)


def test_seed_copies_the_subtree(populated, project):
    _, out = seed(project, "Is the head wave", "--from", populated, "--dry-run")
    assert out.count("- copy") == 4 and not list((project / "tree").glob("*.md"))
    seed(project, "Is the head wave", "--from", populated)
    copies = {p.stem: p.read_text() for p in (project / "tree").glob("*.md")}
    assert len(copies) == 4
    main_uid = re.search(r"nodeInstanceId: (\S+)", (populated / "tree" / "@Head run.md").read_text()).group(1)
    assert "origin: repo@" in copies["@Head run"] and copies["@Head run"].count(main_uid) == 1
    assert "nodeInstanceId: " + main_uid not in copies["@Head run"]
    assert "status: done" in copies["CLM - Head bending is continuously driven"]
    roots = (project / "ideas" / "test-project.md").read_text()
    assert "[[QUE - Is the head wave driven at the head]]" in roots
    assert "— seed" in (project / "NOTEBOOK.md").read_text()
    _, out = run("--vault", project, "check")
    assert "4 nodes, 1 projects, 4 relations, 0 errors" in out
    _, out = seed(project, "Is the head wave", "--from", populated)
    assert out.count("- reuse") == 4 and "0 relations, 0 new roots" in out


def test_seed_depth_and_plain_links(populated, project, tmp_path):
    ygg = lambda *a: run("--vault", populated, *a)
    ygg("new", "question", "Follow up", "--link", "follows-from:Head bending",
        "--body", body(tmp_path, "## Question\n\nSee [[EVD - Innovations travel down the body]].\n"))
    commit(populated, "follow up")
    _, out = seed(project, "Follow up", "--from", populated, "--depth", "0")
    assert out.count("- copy") == 1 and "1 links to notes not copied made plain text" in out
    text = (project / "tree" / "QUE - Follow up.md").read_text()
    assert "See EVD - Innovations travel down the body." in text


def test_seed_needs_a_committed_main_tree(populated, project):
    run("--vault", populated, "log", "uncommitted")  # the notebook does not count
    seed(project, "Is the head wave", "--from", populated)
    run("--vault", populated, "new", "question", "Uncommitted question")
    _, out = seed(project, "Is the head wave", "--from", populated, ok=False)
    assert "uncommitted" in out


def test_compress_maps_seeds_and_is_incremental(populated, project, tmp_path):
    seed(project, "Is the head wave", "--from", populated)
    pygg = lambda *a: run("--vault", project, *a)
    pygg("new", "evidence", "Head wave in a new cohort", "--body", body(tmp_path, EVIDENCE),
         "--link", "informs:Is the head wave", "--link", "derived-from:Head run", "--confidence", "low")
    commit(project.parent.parent, "work")
    _, out = run("--vault", populated, "compress", project)
    assert "(seeded)" in out and "# Seeded from this tree" in out
    assert "[[EVD - Head wave in a new cohort]] informs [[QUE - Is the head wave driven at the head]]" in out
    assert "Since the last compression" not in out
    assert (populated / "tree" / "@proj research tree.md").exists()
    commit(populated, "compressed")

    pygg("new", "question", "Does it hold in larvae", "--link", "follows-from:Head bending")
    pygg("log", "larvae next", "--tag", "idea")
    commit(project.parent.parent, "more")
    _, out = run("--vault", populated, "compress", project)
    since = out.split("# Since the last compression")[1]
    assert "1 notes new, 0 changed, 1 relations new, 1 notebook entries new" in since
    assert "notebook" in since and "larvae next" in since
    assert "(new since the last compression)" in out
    _, out = run("--vault", populated, "show", "@proj research tree")
    assert re.search(r"supersedes \[\[@proj research tree \w+\]\]|is superseded by", out)
    # the new Sources are in no project until compressed nodes derive from them; nothing else is wrong
    _, out = run("--vault", populated, "check")
    assert "2 notes in no project" in out and ", 0 errors" in out


def test_loose_and_out_of_scope_notes(populated, project, tmp_path):
    seed(project, "Is the head wave", "--from", populated)
    pygg = lambda *a, ok=True: run("--vault", project, *a, ok=ok)
    pygg("new", "question", "Do other worms steer the same way")          # a brainstorm left it loose
    pygg("new", "question", "Is the same true of fly larvae", "--link", "follows-from:Head bending",
         "--out-of-scope")
    pygg("set", "Head bending is continuously driven", "--out-of-scope")   # done, yet allowed
    _, out = pygg("set", "Head bending is continuously driven", "--confidence", "low", ok=False)
    assert "frozen" in out
    _, out = pygg("check")
    assert "1 note in no project" in out and "Do other worms" in out and ", 0 errors" in out
    proj = next(p.stem for p in (project / "ideas").glob("*.md"))
    _, out = pygg("report", "--project", proj)
    work, scope = out.split("## Out of scope here")
    assert "## In no project (1)" in work and "Do other worms" in work
    assert "fly larvae" not in work and "fly larvae" in scope and "out of scope)" in scope
    commit(project.parent.parent, "brainstorm")
    _, out = run("--vault", populated, "compress", project)
    out_part = out.split("# Out of scope there (2)")[1].split("# In no project there (1)")
    assert "fly larvae" in out_part[0] and "Head bending" in out_part[0] and "Do other worms" in out_part[1]
    pygg("set", "fly larvae", "--in-scope")
    _, out = pygg("show", "fly larvae")
    assert "out-of-scope" not in out


def test_compress_refuses_uncommitted(populated, project):
    run("--vault", project, "new", "question", "Dirty")
    _, out = run("--vault", populated, "compress", project, ok=False)
    assert "uncommitted changes" in out


@pytest.mark.skipif(not (MAIN_TREE / "ygg.json").exists(), reason="no main tree on this machine")
def test_main_tree_still_checks(tmp_path):
    clone = tmp_path / "main"
    subprocess.run(["git", "clone", "-q", str(MAIN_TREE), str(clone)], check=True)
    run("init", clone)  # upgrades it, if it is in an older format
    _, out = run("--vault", clone, "check")
    assert ", 0 errors" in out


# --- Checking processes ----------------------------------------------------------------

def pid_state(pid, since=None, proc=None):
    """pid_state from a fresh interpreter, optionally with /proc taken away (as on macOS or in a sandbox)."""
    env = dict(os.environ, **({"YGG_PROC": proc} if proc else {}))
    code = ("from importlib.machinery import SourceFileLoader as L; y = L('y', %r).load_module(); "
            "print(y.pid_state(%r, %r))" % (str(ROOT / "scripts" / "ygg"), str(pid), since))
    return subprocess.run([sys.executable, "-c", code], env=env, stdout=subprocess.PIPE,
                          universal_newlines=True, check=True).stdout.strip()


@pytest.mark.parametrize("proc", [None, "/nonexistent"], ids=["proc", "ps"])
def test_pid_state(proc):
    runner = subprocess.Popen(["sleep", "30"])
    zombie = subprocess.Popen(["true"])
    gone = subprocess.Popen(["true"])
    gone.wait()
    time.sleep(0.5)  # zombie has exited but is not reaped
    try:
        assert pid_state(runner.pid, proc=proc) == "running"
        assert pid_state(zombie.pid, proc=proc) == "ended"
        assert pid_state(gone.pid, proc=proc) == "ended"
        # logged an hour before this process started: the PID was reused, so the logged run has ended
        assert pid_state(runner.pid, since=time.time() - 3600, proc=proc) == "ended"
        assert pid_state(runner.pid, since=time.time() - 5, proc=proc) == "running"
        assert pid_state("not-a-pid", proc=proc) == "unknown"
    finally:
        runner.kill()
        zombie.wait()


def test_notebook_writers_do_not_lose_entries(tree):
    procs = [subprocess.Popen([sys.executable, str(ROOT / "scripts" / "ygg"), "--vault", str(tree), "log",
                               "entry %d" % i], stdout=subprocess.DEVNULL) for i in range(20)]
    for p in procs:
        p.wait()
    text = (tree / "NOTEBOOK.md").read_text()
    assert all("entry %d\n" % i in text for i in range(20))
    assert text.count("\n## ") == 20 and "\n\n\n" not in text


def test_init_marks_the_notebook_for_union_merges(tree):
    assert "NOTEBOOK.md merge=union" in (tree / ".gitattributes").read_text()
    run("init", tree)
    assert (tree / ".gitattributes").read_text().count("merge=union") == 1


def test_log_paths_are_stored_relative_to_the_repository(tree):
    sub = tree / "analysis"
    sub.mkdir()
    (sub / "fit.log").write_text("x")
    _, out = run("--vault", tree, "log", "fit", "--pid", str(os.getpid()), "--log", "fit.log",
                 "--log", "/abs/elsewhere.log", cwd=sub)
    assert "log /abs/elsewhere.log does not exist yet" in out
    assert "· logs analysis/fit.log, /abs/elsewhere.log" in (tree / "NOTEBOOK.md").read_text()
    _, out = run("--vault", tree, "log", "x", "--pid", "999999999", cwd=tree)
    assert "is not running here" in out
