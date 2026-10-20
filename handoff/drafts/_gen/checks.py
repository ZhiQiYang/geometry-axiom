# -*- coding: utf-8 -*-
"""Static consistency checks over the generated trees (no compile, no test run).

usage: python checks.py     (after fetch_base.sh and build.py)
env:   REPO (default D:/geometry-axiom), BASE_REV (default 09ab5f79)
"""
import ast
import os
import pathlib
import re
import subprocess

WORK = pathlib.Path(__file__).resolve().parent
BASE = WORK / "base"
REPO = os.environ.get("REPO", "D:/geometry-axiom")
REV = os.environ.get("BASE_REV", "09ab5f79")


def git_show(rel):
    out = subprocess.run(["git", "-C", REPO, "show", REV + ":" + rel], capture_output=True)
    return out.stdout if out.returncode == 0 else None


def read(tree, rel):
    p = WORK / ("out" + tree) / rel
    if p.is_file():
        return p.read_bytes().decode("utf-8", "surrogateescape")
    q = BASE / rel
    if q.is_file():
        return q.read_bytes().decode("utf-8", "surrogateescape")
    data = git_show(rel)
    assert data is not None, rel
    return data.decode("utf-8", "surrogateescape")


def lf(text):
    return text.replace("\r\n", "\n")


problems = []


def check(cond, msg):
    if not cond:
        problems.append(msg)
        print("PROBLEM:", msg)


def mutants_of(text):
    tree = ast.parse(text)
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "dict":
            kw = {k.arg: k.value for k in node.keywords if k.arg}
            if "id" in kw and isinstance(kw["id"], ast.Constant) and re.fullmatch(r"M\d\d", str(kw["id"].value)) and "old" in kw:
                d = {}
                for k, v in kw.items():
                    try:
                        d[k] = ast.literal_eval(v)
                    except Exception:
                        d[k] = None
                result.append(d)
    return result


for name in ("299", "316", "all"):
    outdir = WORK / ("out" + name)
    print("=== tree", name)
    for p in outdir.rglob("*.py"):
        try:
            ast.parse(p.read_bytes().decode("utf-8"))
        except SyntaxError as exc:
            check(False, "syntax %s: %s" % (p.name, exc))
    for p in outdir.rglob("*"):
        if p.suffix in (".c", ".h") and p.is_file():
            code = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'', "",
                          lf(p.read_bytes().decode("utf-8", "surrogateescape")), flags=re.S)
            for a, b in ("{}", "()", "[]"):
                check(code.count(a) == code.count(b), "unbalanced %s%s in %s" % (a, b, p.name))
    ms = mutants_of(read(name, "tests/mutate.py"))
    print("numbered mutants:", len(ms))
    ids = [m["id"] for m in ms]
    check(len(ids) == len(set(ids)), "duplicate mutant ids")
    for m in ms:
        f = m.get("file") or "current_geometry.c"
        n = lf(read(name, f)).count(m["old"])
        if m.get("retired"):
            check(n == 0, "%s retired but anchor present" % m["id"])
        else:
            check(n == 1, "%s anchor count %d in %s" % (m["id"], n, f))
    src = read(name, "tests/test_geo261_wood_contact_world.py")
    cw = read(name, "geometry-templates/woodworking/native/contact_world.c")
    ns = {}
    a = src.index("COLLISION_FILTER = ") if "COLLISION_FILTER = " in src else src.index("STOP_FILTER = ")
    b = src.index("\n\nclass WoodContactWorld")
    exec(compile(src[a:b], "<controls>", "exec"), ns)
    for control in ns["CONTROLS"]:
        check(cw.count(control[1]) == 1, "contact_world control %s anchor count %d" % (control[0], cw.count(control[1])))
    print("contact_world controls:", len(ns["CONTROLS"]))
    wc = read(name, "tests/test_geo261_wood_contacts.py")
    ns2 = {"re": re}
    for node in ast.parse(wc).body:
        if isinstance(node, ast.FunctionDef) and node.name in ("without_comments", "definition", "tokens"):
            exec(compile(ast.Module([node], []), "<fn>", "exec"), ns2)
    contacts = read(name, "geometry-templates/woodworking/native/contacts.c")
    m = re.search(r"controls = \((.*?)\n        \)\n", wc, flags=re.S)
    controls = ast.literal_eval("(" + m.group(1) + ")")
    for ctl in controls:
        original = ns2["definition"](contacts, ctl[1])
        check(original.count(ctl[2]) == 1, "contacts control %s anchor count %d" % (ctl[0], original.count(ctl[2])))
        check(contacts.count(original) == 1, "contacts control %s: original not found verbatim (comment inside function?)" % ctl[0])
    print("contacts controls:", len(controls))
    fixture = git_show("tests/geo261_contacts_legacy_fixture.txt").decode("utf-8").replace("\r\n", "\n")
    s0 = fixture.index("if (has_edge && self->role")
    s1 = fixture.index("ext_end[0]", s0)
    span = ns2["without_comments"](fixture[s0:s1]).strip()
    actual = ns2["definition"](contacts, "wood_member_span_extension_check")
    body = ns2["tokens"](actual[actual.index("{"):])
    guard = ns2["tokens"](span[:span.index("{")])
    if name != "316":
        check(guard == body[1:1 + len(guard)], "guard tokens differ")
        for lit in (x for x in ns2["tokens"](span) if x.startswith('"')):
            check(lit in body, "legacy literal missing: %s" % lit)
    wvt = read(name, "tests/test_geo261_wood_world_validation.py")
    wvc = read(name, "geometry-templates/woodworking/native/world_validation.c")
    mm = re.search(r"controls=\[(.*?)\]\n        for name,before", wvt, flags=re.S)
    ctl_list = ast.literal_eval("[" + mm.group(1) + "]")
    for ctl in ctl_list:
        check(wvc.count(ctl[1]) == 1, "world_validation control %s anchor count %d" % (ctl[0], wvc.count(ctl[1])))
    print("world_validation controls:", len(ctl_list))
    rt = read(name, "tests/run_tests.py")
    tests = None
    for node in ast.parse(rt).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "TESTS":
            tests = ast.literal_eval(node.value)
    expected = read(name, "tests/run_all.expected.json")
    cnt = int(re.search(r'"core:run_tests": \{\s*"mode": "count",\s*"count": (\d+)', expected).group(1))
    check(len(tests) == cnt, "run_all.expected.json core:run_tests %d != TESTS %d" % (cnt, len(tests)))
    print("TESTS", len(tests), "expected", cnt)
    for spec in tests:
        scene = spec["scene"]
        exists = (outdir / scene).is_file() or subprocess.run(["git", "-C", REPO, "cat-file", "-e", REV + ":" + scene]).returncode == 0
        check(exists, "scene file missing: " + scene)
    cwt = read(name, "tests/test_geo261_wood_contact_world.py")
    methods = len(re.findall(r"^    def test_", cwt, flags=re.M))
    exp2 = int(re.search(r'"py:test_geo261_wood_contact_world": \{\s*"mode": "count",\s*"count": (\d+)', expected).group(1))
    check(methods == exp2, "wood_contact_world methods %d != expected %d" % (methods, exp2))
    print("wood_contact_world test methods", methods, "expected", exp2)
    mig = read(name, "tests/test_geo261_mutation_migration.py")
    print("migration len asserts:", re.findall(r"assertEqual\((\d+), len\(added\)\)", mig), "numbered mutants should be 50 + last")

print("PROBLEMS:", len(problems))
