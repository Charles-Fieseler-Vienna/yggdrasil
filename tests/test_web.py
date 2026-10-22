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
        browser.close()
        assert errors == []
