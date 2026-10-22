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


def test_tree_found_below_the_working_folder(tmp_path):
    make_repo(tmp_path / "proj", "research/tree")
    _, out = run("check", cwd=tmp_path / "proj")  # the repository root, with the tree two folders down
    assert "(using the tree in research/tree)" in out and ", 0 errors" in out
    run("init", tmp_path / "proj" / "other")
    _, out = run("check", cwd=tmp_path / "proj", ok=False)
    assert "several trees below it (other, research/tree)" in out
    # outside a git repository (a home folder) nothing below is used
    _, out = run("check", cwd=tmp_path, ok=False)
    assert "no ygg.json in" in out and "run `ygg init`" in out


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
    assert "nodeInstanceId" not in out and "nodeTypeId" not in out and "confidence:" in out
    _, out = ygg("show", "test-project")
    assert out.count("\n- ") == 4
    _, out = ygg("new", "question", "Does it travel", "--link", "follows-from:Is the head wave driven")
    assert out.splitlines()[-1] == "in project test-project"
    _, out = ygg("new", "question", "A loose thought")
    assert "in no project yet" in out
    _, out = ygg("new", "source", "Head run two", "--run", "repo@abc1234:run.sh", "--status", "done")
    assert "joins the projects of the Evidence that derives from it" in out and "--add-root" not in out


def test_sync_fills_in_what_obsidian_leaves_out(populated, ygg):
    q = populated / "tree" / "QUE - Is the head wave driven at the head.md"
    text = q.read_text(encoding="utf-8")
    stripped = re.sub(r"(?m)^(dateCreated|dateModified|completedDate):.*\n|^projects:\n(  - .*\n)*", "", text)
    assert stripped != text
    q.write_text(stripped, encoding="utf-8")
    commit(populated, "a done note made in Obsidian, without dates")
    _, out = ygg("sync")
    assert "1 notes synced" in out
    synced = q.read_text(encoding="utf-8")
    assert '  - "[[test-project]]"' in synced and "dateCreated:" in synced and "completedDate:" in synced
    _, out = ygg("sync")
    assert "0 notes synced" in out
    _, out = ygg("check")
    assert "0 errors" in out
    commit(populated, "synced")
    q.write_text(re.sub(r"dateCreated: .*", "dateCreated: 2020-01-01T00:00:00+00:00", synced), encoding="utf-8")
    _, out = ygg("check", ok=False)
    assert "was done at HEAD and has been changed" in out


def test_schema_export(ygg, tmp_path):
    _, out = ygg("schema")
    data = json.loads(out)
    names = {t["name"] for t in data["nodeTypes"]}
    assert {"Question", "Claim", "Evidence", "Source", "Dataset"} <= names
    assert data["discourseRelations"] and len(data["templates"]) == len(names)
    _, out = ygg("schema", "--out", tmp_path / "s.json")
    assert json.loads((tmp_path / "s.json").read_text(encoding="utf-8")) == data


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


def test_done_outcomes(populated, ygg, tmp_path):
    ygg("new", "evidence", "Pilot fit", "--body", body(tmp_path, EVIDENCE), "--link", "informs:Is the head wave driven")
    ygg("done", "Pilot fit", "--outcome", "inconclusive")  # an alias agents reach for
    assert "outcome: ambiguous" in (populated / "tree" / "EVD - Pilot fit.md").read_text()
    _, out = ygg("done", "Pilot fit", "--outcome", "maybe", ok=False)
    assert "choose from succeeded" in out
    ygg("new", "question", "Does it travel")
    _, out = ygg("done", "Does it travel", "--outcome", "succeeded", ok=False)
    assert "--outcome is for Evidence; a question is done without one" in out
    assert "status: open" in (populated / "tree" / "QUE - Does it travel.md").read_text()
    _, out = ygg("new", "evidence", "Done at once", "--body", body(tmp_path, EVIDENCE), "--status", "done",
                 "--link", "informs:Is the head wave driven", ok=False)
    assert "done evidence needs an outcome (--outcome succeeded" in out
    assert not (populated / "tree" / "EVD - Done at once.md").exists()


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
    ygg("new", "source", "A run", "--run", "repo@abc1234:fit.py", "--data", "results/fit", "--status", "done")
    assert "results/fit" in (tree / "tree" / "@A run.md").read_text()


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


def test_log_for_a_note_without_a_run(populated, ygg):
    ygg("log", "picked this one first", "--tag", "decision", "--for", "Head bending is continuously")
    text = (populated / "NOTEBOOK.md").read_text()
    assert text.rstrip().endswith("picked this one first\n\nfor [[CLM - Head bending is continuously driven]]")
    assert "run id" not in text.split("picked this one first")[1]
    ygg("log", "about [[CLM - Head bending is continuously driven]]", "--for", "CLM - Head bending is continuously driven")
    assert (populated / "NOTEBOOK.md").read_text().rstrip().endswith("about [[CLM - Head bending is continuously driven]]")
    _, out = ygg("log", "fit", "--log", "fit.log", ok=False)
    assert "--log describes a run" in out
    _, out = ygg("log", "picked it", "--tag", "decision", "--on", "Head bending", ok=False)
    assert "use --for NOTE" in out


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


def test_a_run_for_a_note_is_looked_at_once_mentioned(populated, ygg):
    ygg("new", "question", "Does it hold on the full cohort", "--link", "follows-from:Head bending")
    done = subprocess.Popen(["true"])
    done.wait()
    pilot = log_run(ygg, "pilot", "--pid", str(done.pid), "--for", "full cohort")
    ygg("log", "pilot is wired up", "--handoff")
    _, out = ygg("report")
    assert "%s ended" % pilot in out and "is not done" in out  # flagged across the handoff
    _, out = ygg("runs")
    assert pilot in out
    ygg("log", "%s: pipeline check only, not evidence" % pilot)
    _, out = ygg("runs")
    assert out.startswith("No runs")
    _, out = ygg("report")
    assert pilot not in out.split("## Needs action")[-1] or "## Needs action" not in out


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
            f.write("epoch 3\nRuntimeError: CUDA error: out of memory\nbootstrap 10/200\rbootstrap 200/200\n")
        out, _ = watch.communicate(timeout=20)
        lines = out.splitlines()
        assert lines[0].startswith("Watching %s, %s on " % (fit, other)) and "ends when the first ends" in lines[0]
        assert "%s: failure in fit.log: RuntimeError: CUDA error: out of memory" % fit in out
        assert "failure in fit.log: old Traceback" not in out
        assert "%s ended, for [[EVD - Pending fit]].\n  fit.log, last 4 lines:\n" % fit in out
        assert "    RuntimeError: CUDA error: out of memory\n    bootstrap 200/200\n" in out  # a progress bar's end
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
    # a claim always comes with its evidence (and that with its sources), whatever the depth
    _, out = seed(project, "Is the head wave", "--from", populated, "--depth", "1")
    assert "copy [[CLM - Head bending" in out and "copy [[EVD - Innovations travel" in out and "copy [[@Head run]]" in out
    _, out = run("--vault", project, "check")
    assert ", 0 errors" in out


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


def test_compress_maps_seeds_into_a_clone_in_another_folder(populated, project, tmp_path):
    seed(project, "Is the head wave", "--from", populated)
    commit(project.parent.parent, "seeded")
    clone = tmp_path / "elsewhere" / "main-copy"
    subprocess.run(["git", "clone", "-q", str(populated), str(clone)], check=True)
    _, out = run("--vault", clone, "compress", project, "--dry-run")
    assert "(seeded)" in out and "# Seeded from this tree" in out


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
    child = subprocess.Popen(["sleep", "30"])
    try:
        _, out = run("--vault", tree, "log", "fit", "--pid", str(child.pid), "--log", "fit.log",
                     "--log", "/abs/elsewhere.log", cwd=sub)
    finally:
        child.kill()
    assert "log /abs/elsewhere.log does not exist yet" in out
    assert "· logs analysis/fit.log, /abs/elsewhere.log" in (tree / "NOTEBOOK.md").read_text()
    _, out = run("--vault", tree, "log", "x", "--pid", "999999999", cwd=tree)
    assert "is not running here" in out


@pytest.mark.skipif(not os.path.exists("/proc/self/fd"), reason="needs /proc")
def test_log_finds_the_process_writing_the_log(tree):
    """`pgrep -f` finds the agent's own shell, and `$!` after setsid has exited: ygg logs the log's writer."""
    log = tree / "fit.log"
    with log.open("w") as f:
        fit = subprocess.Popen(["sleep", "30"], stdout=f)
    try:
        gone = subprocess.Popen(["true"])
        gone.wait()
        _, out = run("--vault", tree, "log", "fit", "--pid", str(gone.pid), "--log", "fit.log", cwd=tree)
        assert "PID %d is not running here; logging PID %d instead" % (gone.pid, fit.pid) in out
        assert "run id: r%s-%d" % (time.strftime("%y%m%d"), fit.pid) in out
        p = subprocess.run(["sh", "-c", 'exec 3>&-; "$0" "$1" --vault "$2" log shell --pid $$ --log fit.log',
                            sys.executable, str(ROOT / "scripts" / "ygg"), str(tree)], cwd=tree,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        assert "is the shell running this command; logging PID %d instead" % fit.pid in p.stdout
        book = (tree / "NOTEBOOK.md").read_text()
        assert book.count("· pids %d ·" % fit.pid) == 2
        # two steps under setsid: the session's leader runs until both are done, so it is the run
        job = subprocess.Popen(["setsid", "sh", "-c", "sleep 30 > step1.log; sleep 1"], cwd=str(tree))
        try:
            time.sleep(0.5)
            _, out = run("--vault", tree, "log", "job", "--pid", str(gone.pid), "--log", "step1.log", cwd=tree)
            assert "logging PID %d instead" % job.pid in out
        finally:
            subprocess.run(["pkill", "-s", str(job.pid)])
        # with no process writing the log, the PID is kept, with advice
        _, out = run("--vault", tree, "log", "x", "--pid", str(gone.pid), "--log", "other.log", cwd=tree)
        assert "no process here is writing the run's logs" in out and "`$!`" in out
    finally:
        fit.kill()


def test_todos_are_task_lines_ticked_in_place(populated, ygg):
    ygg("log", "Fit converged.", "--todo", "rerun with H=50", "--todo", "plot the residuals")
    ygg("log", "--todo", "ask about the cohort")
    book = populated / "NOTEBOOK.md"
    assert "\n- [ ] rerun with H=50\n- [ ] plot the residuals\n" in book.read_text()
    _, out = ygg("report")
    assert "## To do (3)" in out and "- [ ] ask about the cohort" in out
    _, out = ygg("tick", "nothing like this", ok=False)
    assert "no open to-dos match" in out
    _, out = ygg("tick", "re", ok=False)  # rerun, residuals: say which
    assert "2 open to-dos match" in out
    size = len(book.read_bytes())
    _, out = ygg("tick", "H=50")
    assert "ticked: - [x] rerun with H=50" in out
    assert len(book.read_bytes()) == size and "- [x] rerun with H=50\n- [ ] plot the residuals" in book.read_text()
    ygg("tick", "residuals", "-m", "Plotted; nothing odd.")
    assert "Done: plot the residuals" in book.read_text().split("\n## ")[-1]
    _, out = ygg("report")
    assert "## To do (1)" in out and "H=50" not in out.split("## To do")[1].split("##")[0]


def test_an_issue_is_judged_note_by_note_then_resolved(populated, ygg, tmp_path):
    _, out = ygg("issues")
    assert "No open issues" in out
    _, out = ygg("impact", "Head run")
    assert "2 notes rest on [[@Head run]]" in out
    assert "[[CLM - Head bending is continuously driven]]" in out and "is supported by" in out
    _, out = ygg("log", "x", "--affects", "Head run", ok=False)
    assert "add --issue" in out
    _, out = ygg("log", "Two recordings are all NaN.", "--issue", "--affects", "Head run")
    iid = re.search(r"issue id: (i\d{6}-\d+)", out).group(1)
    assert "- [ ] issue %s · affects [[@Head run]]" % iid in (populated / "NOTEBOOK.md").read_text()
    _, out = ygg("issues")
    assert iid in out and "3 of 3 notes" in out and "still to judge" in out
    _, out = ygg("report")
    assert "## Open issues (1)" in out
    # the evidence is redone (supersede), the claim is judged unaffected in the notebook
    ygg("new", "evidence", "Innovations travel down the body on clean recordings", "--body", body(tmp_path, EVIDENCE),
        "--link", "supersedes:Innovations travel down the body", "--link", "derived-from:Head run",
        "--confidence", "medium")
    ygg("log", "%s: [[CLM - Head bending is continuously driven]] still holds on the clean recordings." % iid)
    _, out = ygg("issues", iid)
    assert "superseded by [[EVD - Innovations travel down the body on clean recordings]]" in out
    assert "[[CLM - Head bending is continuously driven]] (is supported by" in out and ": noted" in out
    assert "[[@Head run]]: to judge" in out and "clean recordings]] (is derived from [[@Head run]]): replaces" in out
    _, out = ygg("resolve", iid, "-m", "Recordings dropped from the cohort.")
    assert "1 note resting on %s has not been judged" % iid in out
    assert "- [x] issue %s" % iid in (populated / "NOTEBOOK.md").read_text()
    _, out = ygg("issues")
    assert "No open issues" in out
    _, out = ygg("issues", "--all")
    assert iid in out and "resolved" in out
    _, out = ygg("resolve", "i000101-9", ok=False)
    assert "no issue i000101-9" in out
    _, out = ygg("check")
    assert "0 errors" in out


def test_ticking_an_issue_box_resolves_it(tree, ygg):
    _, out = ygg("log", "Clock drift in the rig.", "--issue")
    iid = re.search(r"issue id: (i\d{6}-\d+)", out).group(1)
    _, out = ygg("tick", iid, ok=False)  # tick is for to-dos; issues close with resolve
    assert "no open to-dos match" in out
    book = tree / "NOTEBOOK.md"
    book.write_text(book.read_text().replace("- [ ] issue", "- [x] issue"))
    _, out = ygg("issues")
    assert "No open issues" in out


def test_agenda_is_what_a_session_is_pointed_at(populated, ygg):
    from importlib.machinery import SourceFileLoader
    y = SourceFileLoader("ygg_agenda", str(ROOT / "scripts" / "ygg")).load_module()
    ygg("new", "question", "Next question", "--link", "follows-from:Head bending", "--priority", "high")
    ygg("new", "question", "Parked question", "--link", "follows-from:Head bending", "--status", "in-progress")
    ygg("log", "Next up: [[QUE - Next question]], after [[CLM - Head bending is continuously driven]].", "--handoff")
    first = y.agenda(y.Vault(populated))
    assert first == {"QUE - Next question": ["high priority", "named in the last handoff"],
                     "QUE - Parked question": ["in progress"],
                     "CLM - Head bending is continuously driven": ["named in the last handoff"]}
    # a superseded note's work is over: it leaves the agenda and the report's work lists
    ygg("new", "question", "Next question, sharper", "--link", "supersedes:Next question", "--link",
        "follows-from:Head bending")
    first = y.agenda(y.Vault(populated))
    assert first["QUE - Next question"] == ["named in the last handoff"]
    code, out = ygg("set", "Head bending is continuously driven", "--priority", "none", ok=False)
    assert code and "its priority no longer matters" in out and "supersedes" not in out
    _, out = ygg("report")
    work = out.split("## Superseded, not done")[0]
    assert "[[QUE - Next question]]" not in work and "[[QUE - Next question, sharper]]" in work
    assert "[[QUE - Next question]] (open)" in out.split("## Superseded, not done (1)")[1]


def test_watch_flags_nan_losses_not_every_nan():
    from importlib.machinery import SourceFileLoader
    y = SourceFileLoader("ygg_fail", str(ROOT / "scripts" / "ygg")).load_module()
    for line in ("epoch 3 loss=nan", "train_loss: NaN", "grad_norm nan", "NaN detected in layer 2",
                 "Traceback (most recent call last):", "ValueError: bad shape", "Killed"):
        assert y.FAIL_RE.search(line), line
    for line in ("[00] worm5: hilbert_nan=1.0000 med_freq=nan", "nan_frac 0.02", "banana"):
        assert not y.FAIL_RE.search(line), line


def test_a_log_path_given_from_the_tree_folder_falls_back_to_the_repository(tmp_path):
    root = make_repo(tmp_path / "proj", "research/tree")
    (tmp_path / "proj" / "results").mkdir()
    (tmp_path / "proj" / "results" / "fit.log").write_text("start\n")
    _, out = run("log", "fit", "--pid", "1", "--log", "results/fit.log", cwd=root)
    assert "using" in out and "from the repository's top" in out
    assert "logs results/fit.log" in (root / "NOTEBOOK.md").read_text()


def test_questions_for_the_user_wait_until_answered(populated, ygg):
    today = time.strftime("%y%m%d")
    ygg("new", "evidence", "Neural test of the new basis")
    _, out = ygg("log", "Steering passes only under a new definition.", "--ask", "Adopt the new definition?",
                 "--on", "Head bending", "--blocks", "Neural test")
    qid = "a%s-1" % today
    assert "question id: %s" % qid in out
    book = (populated / "NOTEBOOK.md").read_text()
    assert ("- [ ] ask %s · on [[CLM - Head bending is continuously driven]] · blocks "
            "[[EVD - Neural test of the new basis]] · Adopt the new definition?" % qid) in book
    ygg("log", "--ask", "Go on to Stage 5?")
    # a question is not a to-do, and tick leaves it alone
    _, out = ygg("report")
    assert out.startswith("## Waiting on the user (2)") and "## To do" not in out
    code, out = ygg("tick", "Adopt", ok=False)
    assert code and "no open to-dos match" in out
    _, out = ygg("show", "Neural test")
    assert "%s: Adopt the new definition? (blocked until answered)" % qid in out
    ygg("new", "question", "Next", "--priority", "high")
    y = load_module()
    ygg("log", "Next: [[EVD - Neural test of the new basis]]", "--handoff")
    assert y.agenda(y.Vault(populated))["EVD - Neural test of the new basis"] == ["named in the last handoff",
                                                                                  "waiting on the user"]
    _, out = ygg("answer", qid, "-m", "Yes, but report both definitions.")
    assert "— answer" in out
    book = (populated / "NOTEBOOK.md").read_text()
    assert "- [x] ask %s" % qid in book and book.rstrip().endswith("answered %s" % qid)
    _, out = ygg("asks")
    assert qid not in out and "Go on to Stage 5?" in out
    _, out = ygg("report")
    assert "## Answered since the last handoff (1): act on these" in out
    assert re.search(r"  answered \d{4}-\d\d-\d\d \d\d:\d\d: Yes, but report both definitions\.", out)
    first = y.agenda(y.Vault(populated))
    assert "answered by the user" in first["CLM - Head bending is continuously driven"]
    assert "waiting on the user" not in first["EVD - Neural test of the new basis"]
    code, out = ygg("answer", qid, "-m", "No.", ok=False)
    assert code and "answered already" in out
    # a long answer is never cut silently: the report marks the cut, `ygg asks --all` prints it in full
    long = "Accept it with conditions. " + "Condition text. " * 150 + "Last condition."
    ygg("log", "--ask", "Which conditions?")
    ygg("answer", "a%s-3" % today, "-m", long)
    _, out = ygg("report")
    assert "[…] (in full: `ygg asks --all`" in out and "Last condition." not in out
    _, out = ygg("asks", "--all")
    assert "Last condition." in out
    code, out = ygg("log", "x", "--blocks", "Neural test", ok=False)
    assert code and "add --ask" in out
    ygg("log", "done for today", "--handoff")
    _, out = ygg("report")
    assert "Answered since" not in out
    # a decision left to the user in prose is flagged; one asked, or citing a question, is not
    for text in ("Next\n- [ ] read the logs\n- You: accept or reject the new definition",
                 "decision: no Stage 5, still awaiting user acceptance", "**Decision for you:** redefine it?",
                 "- Decide which null is fair (needs the user: it is the whole result)",
                 "The null choice is the open call; I left it for you."):
        _, out = ygg("log", text, "--handoff")
        assert "leaves a decision to the user in prose" in out and "--ask" in out
    for text in ("You were right about the cache; fixed it.", "Still waiting on %s." % qid,
                 "- Your decision (now a question in the report): Stage 5",
                 "This fit needs the user-supplied mask; left it running."):
        _, out = ygg("log", text)
        assert "leaves a decision" not in out


def load_module():
    from importlib.machinery import SourceFileLoader
    return SourceFileLoader("ygg_asks", str(ROOT / "scripts" / "ygg")).load_module()
