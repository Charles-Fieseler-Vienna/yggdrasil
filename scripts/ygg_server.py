"""The ygg web app's server: a FastAPI app over one tree, started by `ygg serve`.

Reads build the graph from the files on every request. Writes run the ygg CLI in a
subprocess, so they pass exactly the checks the CLI applies. /api/events pushes a new
version whenever a note, relations.json or the notebook changes, so edits made in Obsidian
or with the CLI reach the page too. See DESIGN.md, "Web app".
"""
import asyncio
import json
import subprocess
import sys
import threading
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.trustedhost import TrustedHostMiddleware
from watchfiles import DefaultFilter, awatch

WEB_DIR = Path(__file__).resolve().parent / "web"
HOOK = Path(__file__).resolve().parent.parent / "hooks" / "session_start.py"


# --- Reading the tree ------------------------------------------------------------

def tree_version(root):
    """A token that changes whenever a note, relations.json or the notebook does."""
    stamps = [p.stat().st_mtime_ns for d in ("tree", "ideas") if (root / d).is_dir() for p in (root / d).glob("*.md")]
    for name in ("relations.json", "NOTEBOOK.md"):
        if (root / name).exists():
            stamps.append((root / name).stat().st_mtime_ns)
    return "%d-%d" % (len(stamps), max(stamps or [0]))


HIDDEN_META = {"nodeTypeId", "nodeInstanceId", "projects"}  # sent as type, id and projects
RECENT_ENTRIES = 8


def overview_json(ygg, vault):
    """Where the work stands, from the same functions the agent's briefing and `ygg report` use: the
    questions waiting on the user and those answered since the handoff, the agent's list, open to-dos and issues, runs that need someone, the last handoff and recent notebook entries, and
    the briefing itself, word for word as the SessionStart hook gives it."""
    root = vault.root
    entries = ygg.notebook_entries(root)
    hand = [e for e in entries if "handoff" in e["tag"].lower()]
    by_stem = {n.stem: n.uid for n in vault.nodes.values()}
    found = ygg.run_states(vault)
    issues = [{"id": i["id"], "when": i["when"], "title": i["title"],
               "notes": [{"stem": stem, "id": by_stem.get(stem), "how": how, "via": via}
                         for stem, via, how, judged in i["notes"] if not judged],
               "judged": sum(1 for n in i["notes"] if n[3]), "affects": i["affects"]}
              for i in ygg.issue_states(vault) if not i["resolved"]]
    ask = lambda q: {"id": q["id"], "question": q["question"], "context": q["context"], "when": q["when"],
                     "answer": q["answer"], "answered": q["answered"],
                     **{k: [{"stem": x, "id": by_stem.get(x)} for x in q[k]] for k in ("on", "blocks")}}
    try:
        hook = SourceFileLoader("ygg_session_start", str(HOOK)).load_module()
        briefing = "\n".join(hook.summary(ygg, root, root))
    except Exception as e:  # the plugin's hook is not next to this copy of ygg
        briefing = "(could not build the briefing: %s)" % e
    return {"agenda": [{"id": by_stem[s], "stem": s, "why": why} for s, why in ygg.agenda(vault).items()],
            "todos": [t for t in ygg.all_todos(root) if not t["done"]],
            "issues": issues,
            "asks": [ask(q) for q in ygg.all_asks(root) if not q["answer"]],
            "answered": [ask(q) for q in ygg.asks_answered_since_handoff(root)],
            "runs": ygg.runs_summary(found), "needs_action": ygg.needs_action(vault, found),
            "distil": ygg.distil_reminder(vault),
            "handoff": hand[-1] if hand else None,
            "entries": [{"when": e["when"], "tag": e["tag"], "first": (e["text"].splitlines() or [""])[0][:160]}
                        for e in entries[-RECENT_ENTRIES:]][::-1],
            "briefing": briefing}


def graph_json(ygg, vault):
    flags = ygg.node_flags(vault)
    issues = {}  # stem -> open issues whose notes to judge include it
    for i in ygg.issue_states(vault):
        if not i["resolved"]:
            for stem, via, how, judged in i["notes"]:
                if not judged:
                    issues.setdefault(stem, []).append({"id": i["id"], "title": i["title"]})
    asks = {}  # stem -> open questions for the user about it, or blocking it
    for q in ygg.all_asks(vault.root):
        for stem in (q["on"] + q["blocks"]) if not q["answer"] else []:
            asks.setdefault(stem, []).append({"id": q["id"], "question": q["question"], "blocks": stem in q["blocks"]})
    old = {d.stem for rel, s, d in vault.edges() if rel == "supersedes"}
    first = ygg.agenda(vault)
    free = [stem for stem, why in first.items() if not ygg.is_blocked(why)]
    rank = {stem: i + 1 for i, stem in enumerate(free)}  # blocked notes are listed after these, unnumbered
    nodes = [{"id": n.uid, "stem": n.stem, "title": n.content, "type": n.type, "status": n.status,
              "confidence": n.meta.get("confidence"), "outcome": n.meta.get("outcome"),
              "flag": flags.get(n.stem), "issues": issues.get(n.stem, []), "asks": asks.get(n.stem, []), "superseded": n.stem in old,
              "agenda": first.get(n.stem, []), "rank": rank.get(n.stem),
              "projects": [ygg.unlink_name(p) for p in n.meta.get("projects") or []],
              "file": n.path.relative_to(vault.root).as_posix(),
              "meta": {k: v for k, v in n.meta.items() if k not in HIDDEN_META}}
             for n in vault.nodes.values() if n.uid and n.type]
    edges = [{"id": rid, "rel": rel, "source": s.uid, "target": d.uid}
             for rid, rel, s, d in vault.edges(with_ids=True)]
    projects = [{"id": stem, "title": p.meta.get("title") or stem,
                 "roots": [vault.nodes[ygg.unlink_name(r)].uid for r in p.meta.get("roots") or []
                           if ygg.unlink_name(r) in vault.nodes]}
                for stem, p in sorted(vault.projects.items())]
    schema = {"types": {t: {k: v[k] for k in ("name", "prefix", "color", "sections")} for t, v in ygg.TYPES.items()},
              "relations": {r: {"label": v[0], "complement": v[1], "pairs": v[3]} for r, v in ygg.RELATIONS.items()},
              "confidence": ygg.CONFIDENCE, "outcomes": ygg.OUTCOMES, "statuses": ["open", "in-progress"],
              "priorities": ygg.PRIORITIES}
    by_stem = {n.stem: n.uid for n in vault.nodes.values()}
    return {"vault": vault.root.name, "version": tree_version(vault.root), "nodes": nodes, "edges": edges,
            "agenda": [by_stem[s] for s in first if by_stem.get(s)], "agendaOrder": ygg.agenda_order(vault.root),
            "projects": projects, "schema": schema, "errors": vault.errors}


# --- Requests --------------------------------------------------------------------

class NewNode(BaseModel):
    type: str
    title: str
    rel: Optional[str] = None
    other: Optional[str] = None       # the note the new one relates to
    direction: str = "out"            # out: new REL other; in: other REL new
    project: Optional[str] = None     # make it a root of this project instead
    confidence: Optional[str] = None
    zotero: Optional[str] = None      # a paper Source's Zotero item key and DOI
    doi: Optional[str] = None
    sections: Dict[str, str] = {}     # body text by section heading; the type's other sections stay empty


class NewRelation(BaseModel):
    source: str
    rel: str
    target: str


class NodeFields(BaseModel):
    status: Optional[str] = None
    confidence: Optional[str] = None
    priority: Optional[str] = None


class Done(BaseModel):
    outcome: Optional[str] = None


class Order(BaseModel):
    ids: List[str] = []  # notes to put first, in order; none: back to the default order


class Tick(BaseModel):
    text: str


class Answer(BaseModel):
    id: str
    text: str


# --- The app ---------------------------------------------------------------------

class Tree:
    """One tree, and how to run the ygg CLI on it."""

    def __init__(self, ygg, root):
        self.ygg, self.root = ygg, Path(root)
        self.script = Path(ygg.__file__).resolve()
        self.lock = threading.Lock()  # one write at a time

    def vault(self):
        return self.ygg.Vault(self.root)

    def run(self, *argv, body=None):
        """Run `ygg ARGV` on the tree; raise a 400 with its error if it refuses."""
        cmd = [sys.executable, str(self.script), "--vault", str(self.root)] + list(argv)
        if body is not None:
            cmd += ["--body", "-"]
        with self.lock:
            p = subprocess.run(cmd, input=body, capture_output=True, text=True, cwd=str(self.root))
        out = (p.stdout + p.stderr).strip()
        if p.returncode:
            raise HTTPException(400, out.replace("error: ", "", 1))
        print("ygg %s: %s" % (argv[0], out.replace("\n", "; ")), flush=True)
        return out

    def body(self, t, sections):
        """The type's sections, in order, with any text given for them."""
        parts = []
        for name in self.ygg.TYPES[t]["sections"]:
            text = (sections.get(name) or "").strip()
            parts.append("## %s\n" % name + ("\n%s\n" % text if text else ""))
        return "\n".join(parts)


class Uncached(StaticFiles):
    """The page's files, which the browser must check again on every load (a cheap 304 when unchanged):
    without it, a browser keeps running cached modules of an older page after ygg is updated, a mix of old
    and new that fails in odd ways."""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


class TreeFilter(DefaultFilter):
    """Changes to notes, relations.json and the notebook; not .obsidian/ or editor temp files."""

    def __init__(self, root):
        super().__init__()
        self.root = root

    def __call__(self, change, path):
        rel = Path(path).relative_to(self.root).as_posix()
        return super().__call__(change, path) and (
            rel in ("relations.json", "NOTEBOOK.md") or (rel.startswith(("tree/", "ideas/")) and rel.endswith(".md")))


def create_app(ygg, root, token):
    tree = Tree(ygg, root)
    app = FastAPI(title="ygg", docs_url=None, redoc_url=None, openapi_url=None)
    # Against DNS rebinding: only requests addressed to this machine by name.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

    def check_token(x_ygg_token: Optional[str] = Header(None), t: Optional[str] = Query(None)):
        """Other web pages can reach localhost but cannot read the page, so they never learn the token."""
        if (x_ygg_token or t) != token:
            raise HTTPException(403, "missing or wrong token; reload the page")

    api = APIRouter(prefix="/api", dependencies=[Depends(check_token)])

    def node(vault, uid):
        n = vault.by_uid().get(uid)
        if not n:
            raise HTTPException(404, "no note with id %r" % uid)
        return n

    @api.get("/graph")
    def get_graph():
        return graph_json(ygg, tree.vault())

    @api.get("/overview")
    def get_overview():
        return overview_json(ygg, tree.vault())

    @api.post("/todos/tick")
    def tick_todo(q: Tick):
        return {"message": tree.run("tick", q.text)}

    @api.post("/agenda/order")
    def set_order(q: Order):
        vault = tree.vault()
        stems = [node(vault, uid).stem for uid in q.ids]
        return {"message": tree.run("order", "--", *stems) if stems else tree.run("order", "--default")}

    @api.post("/asks/answer")
    def answer_ask(q: Answer):
        return {"message": tree.run("answer", q.id, "-m", q.text)}

    @api.get("/notes/{uid}")
    def get_note(uid: str):
        n = node(tree.vault(), uid)
        return {"id": n.uid, "body": n.body}

    @api.post("/notes")
    def create_note(q: NewNode):
        if q.type not in ygg.TYPES:
            raise HTTPException(400, "type must be one of %s" % ", ".join(ygg.TYPES))
        argv = ["new", q.type, q.title]
        if q.rel and q.other:
            argv += ["--link" if q.direction == "out" else "--link-from", "%s:%s" % (q.rel, q.other)]
        elif not q.project:
            raise HTTPException(400, "a new note needs a relation to another note, or a project to be a root of")
        if q.confidence and q.type in ygg.CONFIDENCE:
            argv += ["--confidence", q.confidence]
        for k in ("zotero", "doi"):
            if getattr(q, k) and getattr(q, k).strip() and q.type == "source":
                argv += ["--" + k, getattr(q, k).strip()]
        tree.run(*argv, body=tree.body(q.type, q.sections))
        prefix = ygg.TYPES[q.type]["prefix"]
        stem = prefix + (q.title[len(prefix):] if q.title.startswith(prefix) else q.title).strip()
        n = tree.vault().nodes.get(stem)
        if n and q.project:
            tree.run("set", q.project, "--add-root", n.uid)
        return {"id": n.uid if n else None}

    @api.patch("/notes/{uid}")
    def set_fields(uid: str, q: NodeFields):
        argv = ["set", uid]
        for k in ("status", "confidence", "priority"):
            if getattr(q, k):
                argv += ["--" + k, getattr(q, k)]
        tree.run(*argv)
        return {"id": uid}

    @api.post("/notes/{uid}/done")
    def mark_done(uid: str, q: Done):
        tree.run("done", uid, *(["--outcome", q.outcome] if q.outcome else []))
        return {"id": uid}

    @api.post("/relations")
    def link(q: NewRelation):
        return {"message": tree.run("link", q.source, q.rel, q.target)}

    @api.delete("/relations/{rid}")
    def unlink(rid: str):
        r = next((e for e in tree.vault().edges(with_ids=True) if e[0] == rid), None)
        if not r:
            raise HTTPException(404, "no relation with id %r" % rid)
        _, rel, s, d = r
        tree.run("unlink", s.uid, rel, d.uid)
        return {}

    @api.get("/events")
    async def events(request: Request):
        """Server-sent events: the tree's version now and after every change."""
        async def stream():
            yield "data: %s\n\n" % json.dumps({"version": tree_version(tree.root)})
            async for changes in awatch(tree.root, watch_filter=TreeFilter(tree.root), yield_on_timeout=True,
                                        rust_timeout=15000, step=200):
                if await request.is_disconnected():
                    break
                # an empty set is a timeout: a comment keeps the connection alive
                yield "data: %s\n\n" % json.dumps({"version": tree_version(tree.root)}) if changes else ": ping\n\n"
        return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-store"})

    app.include_router(api)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTMLResponse((WEB_DIR / "index.html").read_text(encoding="utf-8").replace("{{YGG_TOKEN}}", token),
                            headers={"Cache-Control": "no-store"})

    app.mount("/static", Uncached(directory=str(WEB_DIR)), name="static")
    return app


def serve(ygg, root, port, open_browser):
    import secrets
    import webbrowser

    import uvicorn
    app = create_app(ygg, Path(root).resolve(), secrets.token_urlsafe(24))
    url = "http://localhost:%d/" % port
    print("serving %s at %s; Ctrl-C to stop" % (root, url), flush=True)
    if open_browser:
        threading.Timer(1, webbrowser.open, [url]).start()
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning", timeout_graceful_shutdown=1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
