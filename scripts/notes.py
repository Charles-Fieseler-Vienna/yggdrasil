#!/usr/bin/env python3
"""Create, link, finish and check the notes in this repo.

Every change to a note's frontmatter or Links section goes through this script.
Run `python3 scripts/notes.py <command> -h` for details. Standard library only.
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FOLDERS = {"experiment": "tree", "decision": "tree", "hypothesis": "ideas", "project": "ideas"}
FROZEN_TYPES = {"experiment", "decision"}
TYPES = list(FOLDERS)
STATUSES = ["open", "done"]
OUTCOMES = ["succeeded", "failed", "ambiguous", "promising-out-of-scope"]

# Relation written on the newer note -> inverse shown on the target (generated, never written).
INVERSE = {
    "part_of": "has_part",
    "tests": "tested_by",
    "supports": "supported_by",
    "contradicts": "contradicted_by",
    "depends_on": "needed_by",
    "motivated_by": "motivates",
    "supersedes": "superseded_by",
}
RELATIONS = list(INVERSE)
# (allowed source types, allowed target types) per relation; None means any.
REL_TYPES = {
    "part_of": ({"experiment", "decision", "hypothesis"}, {"project"}),
    "tests": ({"experiment"}, {"hypothesis"}),
    "supports": ({"experiment"}, {"hypothesis"}),
    "contradicts": ({"experiment"}, {"hypothesis"}),
    "depends_on": ({"experiment"}, {"experiment", "decision"}),
    "motivated_by": (None, None),
    "supersedes": (FROZEN_TYPES, FROZEN_TYPES),  # and only within one type
}
# Relations that mean "rests on"; these must not form cycles.
ACYCLIC = {"part_of", "depends_on", "motivated_by", "supersedes"}

FIELD_ORDER = ["id", "type", "title", "status", "outcome", "created",
               "run_start", "run_end", "run", "data", "figures", "refs", "legacy_ref"]
LIST_FIELDS = {"data", "figures", "refs"}
COMMON = {"id", "type", "title", "created", "refs", "legacy_ref"}
TYPE_FIELDS = {
    "experiment": COMMON | {"status", "outcome", "run_start", "run_end", "run", "data", "figures"},
    "decision": COMMON | {"status"},
    "hypothesis": COMMON,
    "project": COMMON,
}

TEMPLATES = {
    "experiment": "## Purpose\n\n<!-- What question this run answers, and what result was expected. -->\n\n"
                  "## Method\n\n## Results\n\n<!-- Key numbers, with n and cohort. -->\n\n"
                  "## Conclusion\n\n<!-- Required before `done`. -->\n\n## Caveats\n",
    "decision": "## Context\n\n<!-- What forced a choice. -->\n\n"
                "## Decision\n\n<!-- Required before `done`. -->\n\n"
                "## Rationale\n\n## Alternatives considered\n",
    "hypothesis": "## Question\n\n<!-- One question, smaller than a project. -->\n\n"
                  "## Prediction\n\n<!-- What result would support it, and what would refute it. -->\n",
    "project": "## Summary\n\n"
               "## Findings\n\n<!-- The project's current conclusions. Each cites the experiments it rests on, "
               "e.g. \"... ([[exp-a]], [[exp-b]])\". Revise freely; the experiments hold the frozen record. -->\n\n"
               "## Decisions\n\n<!-- The decisions that shape this project, linked inline. Minor practical "
               "decisions need not be listed here; they are part_of the project and appear below. -->\n\n"
               "```dataview\nTABLE status FROM [[]] WHERE type = \"decision\" SORT created\n```\n\n"
               "## Hypotheses\n\n```dataview\nLIST FROM [[]] WHERE type = \"hypothesis\"\n```\n\n"
               "## Experiments\n\n```dataview\nTABLE status, outcome, legacy_ref FROM [[]] "
               "WHERE type = \"experiment\" SORT created\n```\n",
}

ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REF_RE = re.compile(r"^[\w.-]+@[0-9a-f]{7,40}:\S+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
LINK_ITEM_RE = re.compile(r"^- \[\[([^\]|#]+)\]\](?:\s+—\s+(.*))?$")
CODE_BLOCK_RE = re.compile(r"```.*?```", re.S)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
PLAIN_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./@:+-]*$")
YAML_AMBIGUOUS_RE = re.compile(r"^([-+]?[\d.]+([eE][-+]?\d+)?|true|false|yes|no|on|off|null|~)$", re.I)


class NoteError(Exception):
    pass


# --- Parsing and rendering ---------------------------------------------------

def parse_scalar(v):
    return json.loads(v) if v.startswith('"') else v


def format_scalar(v):
    v = str(v)
    if PLAIN_RE.match(v) and not YAML_AMBIGUOUS_RE.match(v):
        return v
    return json.dumps(v, ensure_ascii=False)


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        raise NoteError("missing frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise NoteError("unterminated frontmatter")
    meta, key = {}, None
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if line.startswith("  - "):
            if key is None or not isinstance(meta[key], list):
                raise NoteError("list item without a list field: " + line)
            meta[key].append(parse_scalar(line[4:].strip()))
            continue
        k, sep, v = line.partition(":")
        if not sep:
            raise NoteError("bad frontmatter line: " + line)
        key, v = k.strip(), v.strip()
        meta[key] = [] if v in ("", "[]") else parse_scalar(v)
    return meta, text[end + 5:]


def split_links(body):
    """Split a body into (prose, links); links are (rel, target, annotation) tuples."""
    m = re.search(r"^## Links[ \t]*$", body, re.M)
    if not m:
        return body.strip() + "\n", []
    rest = body[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    section, after = (rest[:nxt.start()], rest[nxt.start():]) if nxt else (rest, "")
    links, rel = [], None
    for line in section.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("### "):
            rel = s[4:].strip()
            continue
        item = LINK_ITEM_RE.match(s)
        if not item or rel is None:
            raise NoteError("unparseable line in Links section: " + s)
        links.append((rel, item.group(1).strip(), (item.group(2) or "").strip()))
    prose = (body[:m.start()].strip() + "\n\n" + after.strip()).strip()
    return prose + "\n", links


def section_text(prose, heading):
    """Text under `## heading`, without HTML comments; None if the heading is missing."""
    m = re.search(r"^## %s[ \t]*$" % re.escape(heading), prose, re.M)
    if not m:
        return None
    rest = prose[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return COMMENT_RE.sub("", rest[:nxt.start()] if nxt else rest).strip()


def inline_links(prose):
    return [t.strip() for t in WIKILINK_RE.findall(COMMENT_RE.sub("", CODE_BLOCK_RE.sub("", prose)))]


class Note:
    def __init__(self, path, meta, prose, links):
        self.path, self.meta, self.prose, self.links = path, meta, prose, links

    id = property(lambda self: self.meta.get("id"))
    type = property(lambda self: self.meta.get("type"))
    status = property(lambda self: self.meta.get("status"))
    title = property(lambda self: self.meta.get("title", ""))

    @classmethod
    def from_text(cls, path, text):
        meta, body = parse_frontmatter(text)
        prose, links = split_links(body)
        return cls(path, meta, prose, links)

    @classmethod
    def load(cls, path):
        return cls.from_text(path, path.read_text(encoding="utf-8"))

    def render(self):
        lines = ["---"]
        keys = FIELD_ORDER + sorted(k for k in self.meta if k not in FIELD_ORDER)
        for k in keys:
            v = self.meta.get(k)
            if v is None or v == "" or v == []:
                continue
            if isinstance(v, list):
                lines.append(k + ":")
                lines += ["  - " + format_scalar(x) for x in v]
            else:
                lines.append(k + ": " + format_scalar(v))
        lines.append("---")
        out = "\n".join(lines) + "\n\n" + self.prose.strip() + "\n"
        if self.links:
            out += "\n## Links\n"
            for rel in RELATIONS:
                items = [(t, a) for r, t, a in self.links if r == rel]
                if items:
                    out += "\n### " + rel + "\n"
                    out += "".join("- [[%s]]%s\n" % (t, " — " + a if a else "") for t, a in items)
        return out

    def save(self):
        self.path.write_text(self.render(), encoding="utf-8")


def load_all():
    notes, errors = {}, []
    for folder in sorted(set(FOLDERS.values())):
        for p in sorted((ROOT / folder).iterdir()):
            if p.name == ".gitkeep":
                continue
            if p.suffix != ".md":
                errors.append("%s: only .md notes belong here; this repo is text only" % relpath(p))
                continue
            try:
                notes[p.stem] = Note.load(p)
            except (NoteError, ValueError) as e:
                errors.append("%s: %s" % (relpath(p), e))
    return notes, errors


def relpath(p):
    return str(p.relative_to(ROOT))


# --- Validation ----------------------------------------------------------------

def validate(n, notes):
    errs = []
    m, t = n.meta, n.type
    if n.id != n.path.stem:
        errs.append("id %r does not match filename" % n.id)
    if not n.id or not ID_RE.match(n.id):
        errs.append("id %r is not a lowercase-hyphen slug" % n.id)
    if t not in TYPES:
        return errs + ["type %r is not one of %s" % (t, TYPES)]
    if n.path.parent.name != FOLDERS[t]:
        errs.append("type %s belongs in %s/" % (t, FOLDERS[t]))
    if not n.title:
        errs.append("missing title")
    for k in sorted(set(m) - TYPE_FIELDS[t]):
        errs.append("field %r is not allowed on a %s" % (k, t))
    for k in LIST_FIELDS & set(m):
        if not isinstance(m[k], list):
            errs.append("field %r must be a list" % k)
    if not DATE_RE.match(str(m.get("created", ""))):
        errs.append("created must be YYYY-MM-DD")

    if t == "experiment":
        if n.status not in STATUSES:
            errs.append("status %r is not one of %s" % (n.status, STATUSES))
        if "outcome" in m and m["outcome"] not in OUTCOMES:
            errs.append("outcome %r is not one of %s" % (m["outcome"], OUTCOMES))
        for k in ("run_start", "run_end"):
            if k in m and not DATETIME_RE.match(str(m[k])):
                errs.append("%s must be YYYY-MM-DD or YYYY-MM-DDTHH:MM" % k)
        if "run" in m and not REF_RE.match(str(m["run"])):
            errs.append("run must be repository@commit:path, got %r" % m["run"])
        for f in m.get("figures") or []:
            if not (REF_RE.match(f) or f.startswith("/")):
                errs.append("figure %r must be repository@commit:path or an absolute cluster path" % f)
        if n.status == "done":
            if not m.get("outcome"):
                errs.append("a done experiment needs an outcome")
            if not m.get("run"):
                errs.append("a done experiment needs a run reference")
            if not section_text(n.prose, "Conclusion"):
                errs.append("a done experiment needs a non-empty ## Conclusion section")

    if t == "decision":
        if n.status not in STATUSES:
            errs.append("status %r is not one of %s" % (n.status, STATUSES))
        if n.status == "done" and not section_text(n.prose, "Decision"):
            errs.append("a done decision needs a non-empty ## Decision section")

    if t in FROZEN_TYPES and not any(r == "part_of" for r, _, _ in n.links):
        errs.append("a %s must be part_of at least one project" % t)

    seen = set()
    for rel, target, _ in n.links:
        if rel not in INVERSE:
            errs.append("unknown relation %r" % rel)
            continue
        if (rel, target) in seen:
            errs.append("duplicate link %s [[%s]]" % (rel, target))
        seen.add((rel, target))
        if target == n.id:
            errs.append("links to itself")
        tn = notes.get(target)
        if tn is None:
            errs.append("link target [[%s]] does not exist" % target)
            continue
        sources, targets = REL_TYPES[rel]
        if (sources and t not in sources) or (targets and tn.type not in targets):
            errs.append("%s goes from %s to %s, not %s to %s" % (
                rel, "/".join(sorted(sources or ["any"])), "/".join(sorted(targets or ["any"])), t, tn.type))
        elif rel == "supersedes" and tn.type != t:
            errs.append("supersedes must stay within one type, not %s to %s" % (t, tn.type))
    for target in inline_links(n.prose):
        if target not in notes:
            errs.append("inline link [[%s]] does not exist" % target)
    return errs


def cycle_errors(notes):
    graph = {nid: [tg for r, tg, _ in n.links if r in ACYCLIC and tg in notes] for nid, n in notes.items()}
    state, errs = {}, []

    def visit(v, stack):
        state[v] = 1
        for w in graph[v]:
            if state.get(w) == 1:
                errs.append("cycle: " + " -> ".join(stack[stack.index(w):] + [w]))
            elif w not in state:
                visit(w, stack + [w])
        state[v] = 2

    for v in graph:
        if v not in state:
            visit(v, [v])
    return errs


def cited_by_projects(notes):
    """Map note id -> projects whose ## Findings section cites it."""
    cited = defaultdict(list)
    for n in notes.values():
        if n.type == "project":
            for target in inline_links(section_text(n.prose, "Findings") or ""):
                cited[target].append(n.id)
    return cited


def uncited(notes):
    cited = cited_by_projects(notes)
    return [n for n in notes.values() if n.type == "experiment" and n.status == "done" and not cited[n.id]]


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT)] + list(args), check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          universal_newlines=True).stdout


def frozen_errors():
    """Experiments and decisions that were done at HEAD must not be modified, renamed or deleted."""
    try:
        diff = git("diff", "--name-status", "HEAD", "--", *sorted({FOLDERS[t] for t in FROZEN_TYPES}))
    except (subprocess.CalledProcessError, OSError):
        return []  # no git, or no commit yet
    errs = []
    for line in diff.splitlines():
        parts = line.split("\t")
        if parts[0].startswith("A"):
            continue
        try:
            meta, _ = parse_frontmatter(git("show", "HEAD:" + parts[1]))
        except (subprocess.CalledProcessError, NoteError):
            continue
        if meta.get("status") == "done":
            errs.append("%s: was done at HEAD and has been changed; supersede it instead" % parts[1])
    return errs


def incoming_links(notes):
    inc = defaultdict(list)
    for n in notes.values():
        for rel, target, ann in n.links:
            if rel in INVERSE:
                inc[target].append((INVERSE[rel], n.id, ann))
    return inc


# --- Commands ------------------------------------------------------------------

def die(msg):
    sys.exit("error: " + msg)


def today():
    return datetime.date.today().isoformat()


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60].rsplit("-", 1)[0] if len(s) > 60 else s


def parse_link(spec):
    rel, sep, rest = spec.partition(":")
    if not sep:
        die("--link must be REL:TARGET or REL:TARGET:ANNOTATION, got %r" % spec)
    target, _, ann = rest.partition(":")
    return rel.strip(), target.strip(), ann.strip()


def read_body(path):
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")


def with_title(prose, title):
    prose = prose.strip() + "\n"
    if "\n## Links" in "\n" + prose:
        die("give links with --link, not inside --body")
    return prose if prose.startswith("# ") else "# %s\n\n%s" % (title, prose)


def save_checked(note, notes):
    notes = dict(notes)
    notes[note.path.stem] = note
    errs = validate(note, notes)
    if errs:
        die("%s:\n  " % relpath(note.path) + "\n  ".join(errs))
    note.save()
    print(relpath(note.path))


def get_editable(notes, nid):
    n = notes.get(nid)
    if n is None:
        die("no note %r" % nid)
    if n.status == "done":
        die("%s is done and frozen; create a new %s that supersedes it" % (nid, n.type))
    return n


def cmd_new(a):
    notes, _ = load_all()
    nid = a.id or slugify(a.title)
    if nid in notes:
        die("a note with id %r already exists" % nid)
    meta = {"id": nid, "type": a.type, "title": a.title, "created": a.created or today()}
    if a.type in FROZEN_TYPES:
        meta["status"] = "open"
    for k in ("run", "run_start", "run_end", "legacy_ref"):
        if getattr(a, k):
            meta[k] = getattr(a, k)
    for k, vals in (("data", a.data), ("figures", a.figure), ("refs", a.ref)):
        if vals:
            meta[k] = vals
    prose = with_title(read_body(a.body) if a.body else TEMPLATES[a.type], a.title)
    path = ROOT / FOLDERS[a.type] / (nid + ".md")
    save_checked(Note(path, meta, prose, [parse_link(s) for s in a.link]), notes)


def cmd_link(a):
    notes, _ = load_all()
    n = get_editable(notes, a.id)
    n.links.append((a.rel, a.target, a.note or ""))
    save_checked(n, notes)


def cmd_unlink(a):
    notes, _ = load_all()
    n = get_editable(notes, a.id)
    kept = [l for l in n.links if (l[0], l[1]) != (a.rel, a.target)]
    if len(kept) == len(n.links):
        die("%s has no link %s [[%s]]" % (a.id, a.rel, a.target))
    n.links = kept
    save_checked(n, notes)


def cmd_set(a):
    notes, _ = load_all()
    n = get_editable(notes, a.id)
    for k in ("title", "run", "run_start", "run_end", "legacy_ref"):
        if getattr(a, k):
            n.meta[k] = getattr(a, k)
    for k, vals in (("data", a.add_data), ("figures", a.add_figure), ("refs", a.add_ref)):
        for v in vals:
            n.meta.setdefault(k, [])
            if v not in n.meta[k]:
                n.meta[k].append(v)
    if a.body:
        n.prose = with_title(read_body(a.body), n.title)
    save_checked(n, notes)


def cmd_done(a):
    notes, _ = load_all()
    n = get_editable(notes, a.id)
    if n.type not in FROZEN_TYPES:
        die("only experiments and decisions are frozen; hypotheses and projects stay editable")
    if (n.type == "experiment") != bool(a.outcome):
        die("--outcome is required for experiments and not allowed for decisions")
    n.meta["status"] = "done"
    if a.outcome:
        n.meta["outcome"] = a.outcome
    save_checked(n, notes)


def cmd_show(a):
    notes, _ = load_all()
    n = notes.get(a.id)
    if n is None:
        die("no note %r" % a.id)
    print(n.path.read_text(encoding="utf-8").rstrip())
    inc = incoming_links(notes)[a.id]
    if inc:
        print("\n<!-- incoming (generated) -->")
        for rel, src, ann in sorted(inc):
            print("- %s [[%s]]%s" % (rel, src, " — " + ann if ann else ""))


def cmd_report(a):
    notes, _ = load_all()
    inc = incoming_links(notes)
    verdict = ("tested_by", "supported_by", "contradicted_by")
    groups = [
        ("Open experiments", [n for n in notes.values() if n.type == "experiment" and n.status == "open"]),
        ("Open decisions", [n for n in notes.values() if n.type == "decision" and n.status == "open"]),
        ("Done experiments not (yet) cited by any project's Findings", uncited(notes)),
        ("Untested hypotheses", [n for n in notes.values() if n.type == "hypothesis"
                                 and not any(r in verdict for r, _, _ in inc[n.id])]),
    ]
    for title, group in groups:
        print("## %s (%d)" % (title, len(group)))
        for n in sorted(group, key=lambda n: (str(n.meta.get("created")), n.id)):
            projects = [t for r, t, _ in n.links if r == "part_of"]
            print("- %s: %s [%s]" % (n.id, n.title, ", ".join(projects) or "no project"))
        print()


def cmd_check(a):
    notes, errors = load_all()
    for n in notes.values():
        errors += ["%s: %s" % (relpath(n.path), e) for e in validate(n, notes)]
    errors += cycle_errors(notes) + frozen_errors()
    for e in errors:
        print(e)
    print("%d notes, %d errors" % (len(notes), len(errors)))
    sys.exit(1 if errors else 0)


# --- CLI -----------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    link_help = "REL:TARGET[:ANNOTATION], repeatable. REL is one of: " + ", ".join(RELATIONS)

    p = sub.add_parser("new", help="create a note")
    p.add_argument("type", choices=TYPES)
    p.add_argument("title")
    p.add_argument("--id", help="slug; defaults to one made from the title")
    p.add_argument("--link", action="append", default=[], help=link_help)
    p.add_argument("--body", help="markdown file with the prose sections, or - for stdin")
    p.add_argument("--ref", action="append", default=[], help="citation key, repeatable")
    p.add_argument("--data", action="append", default=[], help="data location, repeatable (experiments)")
    p.add_argument("--figure", action="append", default=[],
                   help="repository@commit:path or absolute cluster path, repeatable (experiments)")
    p.add_argument("--run", help="repository@commit:path to the run script (experiments)")
    p.add_argument("--run-start", dest="run_start")
    p.add_argument("--run-end", dest="run_end")
    p.add_argument("--created", help="YYYY-MM-DD; defaults to today (use when backfilling)")
    p.add_argument("--legacy-ref", dest="legacy_ref")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("link", help="add a link to an editable note")
    p.add_argument("id")
    p.add_argument("rel", choices=RELATIONS)
    p.add_argument("target")
    p.add_argument("--note", help="one-line annotation explaining the link")
    p.set_defaults(func=cmd_link)

    p = sub.add_parser("unlink", help="remove a link from an editable note")
    p.add_argument("id")
    p.add_argument("rel", choices=RELATIONS)
    p.add_argument("target")
    p.set_defaults(func=cmd_unlink)

    p = sub.add_parser("set", help="change fields or the body of an editable note")
    p.add_argument("id")
    p.add_argument("--title")
    p.add_argument("--run")
    p.add_argument("--run-start", dest="run_start")
    p.add_argument("--run-end", dest="run_end")
    p.add_argument("--legacy-ref", dest="legacy_ref")
    p.add_argument("--add-data", action="append", default=[])
    p.add_argument("--add-figure", action="append", default=[])
    p.add_argument("--add-ref", action="append", default=[])
    p.add_argument("--body", help="replace the prose sections from a file, or - for stdin")
    p.set_defaults(func=cmd_set)

    p = sub.add_parser("done", help="freeze an experiment or decision")
    p.add_argument("id")
    p.add_argument("--outcome", choices=OUTCOMES, help="required for experiments")
    p.set_defaults(func=cmd_done)

    p = sub.add_parser("show", help="print a note with its generated incoming links")
    p.add_argument("id")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("report", help="list open experiments and decisions, uncited experiments and untested hypotheses")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("check", help="validate all notes; exit 1 on any error")
    p.set_defaults(func=cmd_check)

    a = ap.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
