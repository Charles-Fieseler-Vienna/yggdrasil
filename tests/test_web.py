"""The web app in a real browser. Slow and needs uv, Playwright and Chrome; run with YGG_WEB_TESTS=1:
YGG_WEB_TESTS=1 uv run --no-project --with pytest --with playwright pytest tests/test_web.py"""
import os
import re
import shutil
import socket
import subprocess
import time

import pytest

from conftest import ROOT, body, EVIDENCE, CLAIM

pytestmark = pytest.mark.skipif(os.environ.get("YGG_WEB_TESTS") != "1" or not shutil.which("uv"),
                                reason="set YGG_WEB_TESTS=1 (needs uv, Playwright and Chrome)")


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server(populated):
    port = free_port()
    proc = subprocess.Popen([str(ROOT / "bin" / "ygg"), "--vault", str(populated), "serve", "--port", str(port)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    url = "http://localhost:%d/" % port
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            break
        except OSError:
            time.sleep(0.5)
    yield url, populated
    proc.terminate()
    proc.wait(10)


def test_page_shows_and_edits_the_tree(server):
    from playwright.sync_api import sync_playwright
    url, tree = server
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(url)
        page.wait_for_selector(".react-flow__node", timeout=20000)
        assert page.locator(".react-flow__node", has_text="Is the head wave driven").count() == 1
        claim = page.locator(".react-flow__node", has_text="Head bending is continuously driven")
        assert claim.count() == 1  # top questions start unfolded
        page.locator(".react-flow__node", has_text="Is the head wave driven").click(modifiers=["Control"])
        page.wait_for_timeout(800)
        assert claim.count() == 0
        page.locator(".react-flow__node", has_text="Is the head wave driven").click(modifiers=["Control"])
        page.wait_for_timeout(800)
        assert claim.count() == 1
        # a CLI change reaches the open page
        subprocess.run([str(ROOT / "bin" / "ygg"), "--vault", str(tree), "new", "question", "Made from the CLI",
                        "--link", "follows-from:Head bending"], check=True, stdout=subprocess.PIPE)
        page.wait_for_function("() => window.__G && window.__G.byStem.has('QUE - Made from the CLI')", timeout=10000)
        page.fill(".search", "QUE - Made from the CLI")  # search takes a full filename
        page.wait_for_timeout(1000)
        assert "Made from the CLI" in page.inner_text(".panel")
        # the overview: what the agent is told, to-dos ticked from the page, priority set from the page
        ygg = lambda *a: subprocess.run([str(ROOT / "bin" / "ygg"), "--vault", str(tree)] + list(a), check=True,
                                        stdout=subprocess.PIPE)
        ygg("log", "Next: [[QUE - Made from the CLI]].", "--handoff", "--todo", "plot the residuals")
        page.click("text=Overview")
        page.wait_for_selector(".overview .todos input", timeout=10000)
        panel = page.inner_text(".panel")
        assert "named in the last handoff" in panel and "plot the residuals" in panel
        page.locator(".overview .todos input").first.click()
        page.wait_for_function("() => !document.querySelector('.overview .todos')", timeout=10000)
        assert "- [x] plot the residuals" in (tree / "NOTEBOOK.md").read_text()
        page.select_option(".overview select.inline", "high")
        page.wait_for_selector(".note .prio-badge", timeout=10000)
        assert "priority: high" in (tree / "tree" / "QUE - Made from the CLI.md").read_text()
        # the frontier: only open notes and gaps, cut loose from the done ones above them
        page.select_option(".note-filter select", "frontier")
        page.wait_for_timeout(1000)
        assert page.locator(".react-flow__node").count() == 1
        assert "after Head bending is continuously driven" in page.inner_text(".react-flow__node")
        page.select_option(".note-filter select", "")
        # superseded notes are hidden by default, their replacement taking their place
        ygg("new", "evidence", "Innovations travel down the body, redone", "--link", "supersedes:Innovations travel",
            "--link", "supports:Head bending")
        page.wait_for_function("() => window.__G.byStem.has('EVD - Innovations travel down the body, redone')",
                               timeout=10000)
        page.click("text=Unfold all")
        page.wait_for_timeout(1000)
        assert page.locator(".react-flow__node", has_text="redone").count() == 1
        assert page.locator(".react-flow__node", has_text="Innovations travel down the body").count() == 1
        page.click(".superseded-chip")
        page.wait_for_timeout(1000)
        assert page.locator(".note.superseded").count() == 1
        # a question for the user: first in the overview, a badge on its note, answered from the page
        ygg("log", "--ask", "Adopt the new definition?", "--on", "Head bending")
        page.click("text=Overview")
        page.wait_for_selector(".overview .ask textarea", timeout=10000)
        assert page.locator(".note .ask-badge").count() == 1
        assert page.inner_text(".overview h3 >> nth=0").lower().startswith("waiting on you")
        page.fill(".overview .ask textarea", "Yes, and report both.")
        page.click(".overview .ask button")
        page.wait_for_function("() => !document.querySelector('.overview .ask')", timeout=10000)
        book = (tree / "NOTEBOOK.md").read_text()
        assert "Yes, and report both.\n\nanswered a" in book and "- [x] ask a" in book
        assert "answered since the last handoff" in page.inner_text(".panel").lower()
        assert page.locator(".note .ask-badge").count() == 0
        browser.close()
        assert errors == []


def test_agenda_order_and_dragging(server):
    from playwright.sync_api import sync_playwright
    url, tree = server
    ygg = lambda *a: subprocess.run([str(ROOT / "bin" / "ygg"), "--vault", str(tree)] + list(a), check=True,
                                    stdout=subprocess.PIPE)
    ygg("new", "question", "Alpha", "--link", "follows-from:Head bending", "--priority", "high")
    ygg("new", "question", "Beta", "--link", "follows-from:Head bending", "--status", "in-progress")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(url)
        page.wait_for_selector(".overview ol.agenda", timeout=20000)
        first = lambda: page.inner_text(".overview ol.agenda li >> nth=0")
        assert "Beta" in first()  # in progress before high priority
        # the user's order, by dragging a row: into the notebook, and the list follows it
        rows = page.locator(".overview ol.agenda li")
        rows.nth(1).locator(".grip").drag_to(rows.nth(0))
        assert "Alpha" in first()
        page.click("button:has-text('Save order')")
        page.wait_for_selector(".agenda-order:has-text('The first 2')", timeout=10000)
        assert "Alpha" in first()
        assert "1. [[QUE - Alpha]]\n2. [[QUE - Beta]]" in (tree / "NOTEBOOK.md").read_text()
        page.click("button:has-text('Default order')")
        page.wait_for_selector(".agenda-order:has-text('In the default order:')", timeout=10000)
        assert "Beta" in first()
        rows.nth(0).hover()
        rows.nth(0).locator("button[title=Down]").click()
        assert "Alpha" in first()
        page.click("button:has-text('Cancel')")
        assert "Beta" in first()
        # a blocked note: below the numbered ones, with a dash
        ygg("link", "Alpha", "blocked-by", "Beta")
        page.wait_for_selector(".overview li.blocked:has-text('Alpha')", timeout=10000)
        assert page.inner_text(".overview li.blocked .rank") == "–"
        # edges survive folding and unfolding, every time (React Flow once lost them on every other change)
        root = page.locator(".react-flow__node", has_text="Is the head wave driven")
        edges = page.locator(".react-flow__edge").count()
        assert edges > 0
        for _ in range(4):
            root.click(modifiers=["Control"])
            page.wait_for_timeout(700)
        assert page.locator(".react-flow__edge").count() == edges
        # a dragged card keeps its place, across a reload, until the positions are reset
        card = page.locator(".react-flow__node", has_text="Head bending is continuously driven")
        box = card.bounding_box()
        page.mouse.move(box["x"] + 20, box["y"] + 10)
        page.mouse.down()
        page.mouse.move(box["x"] + 140, box["y"] + 90, steps=12)
        page.mouse.up()
        moved = card.bounding_box()
        assert moved["x"] - box["x"] > 100 and moved["y"] - box["y"] > 60
        assert page.locator(".react-flow__edge").count() == edges
        page.reload()
        page.wait_for_selector("button:has-text('Reset positions')", timeout=20000)
        page.click("button:has-text('Reset positions')")
        assert page.locator("button:has-text('Reset positions')").count() == 0
        browser.close()
        assert errors == []


def test_the_page_is_never_run_from_a_stale_cache(server):
    """After an update, a browser must not keep running cached modules of the old page."""
    import urllib.request
    url, _ = server
    for path, policy in (("", "no-store"), ("static/main.js", "no-cache"), ("static/panel.js", "no-cache")):
        with urllib.request.urlopen(url + path) as r:
            assert r.headers["Cache-Control"] == policy, path
