# -*- coding: utf-8 -*-
"""Which axiom-reader trace entries (code sites / scenes / mutants / light) change with each patch variant?

Uses geometry-guide/axiom_matrix.py and the clause list of the base commit; reads only git and ./out*.
usage: python reader_impact.py     env: REPO, BASE_REV
"""
import glob
import os
import pathlib
import re
import subprocess
import tarfile
import tempfile
import types

WORK = pathlib.Path(__file__).resolve().parent
REPO = os.environ.get("REPO", "D:/geometry-axiom")
REV = os.environ.get("BASE_REV", "09ab5f79")


def git_show(rel):
    return subprocess.run(["git", "-C", REPO, "show", REV + ":" + rel], capture_output=True, check=True).stdout


am = types.ModuleType("axiom_matrix")
am.__file__ = str(WORK / "axiom_matrix.py")   # the module computes ROOT from __file__; only its pure functions are used here
exec(compile(git_show("geometry-guide/axiom_matrix.py").decode("utf-8").replace("\r\n", "\n"), "axiom_matrix.py", "exec"), am.__dict__)
axiom = git_show("公理層.md").decode("utf-8").replace("\r\n", "\n")
clauses = am.parse_clauses(axiom)
ids = [c[0] for c in clauses]

scene_dir = tempfile.mkdtemp(prefix="scenes-")
archive = subprocess.run(["git", "-C", REPO, "archive", REV, ":(glob)*.scene"], capture_output=True, check=True).stdout
with tempfile.NamedTemporaryFile(delete=False, suffix=".tar") as handle:
    handle.write(archive)
with tarfile.open(handle.name) as tar:
    tar.extractall(scene_dir)


def trace(tree):
    outdir = WORK / ("out" + tree) if tree else None
    cg = outdir / "current_geometry.c" if outdir else None
    src = (cg.read_bytes() if cg is not None and cg.is_file() else git_show("current_geometry.c")).decode("utf-8", "replace")
    mu = outdir / "tests/mutate.py" if outdir else None
    mut = (mu.read_bytes() if mu is not None and mu.is_file() else git_show("tests/mutate.py")).decode("utf-8")
    scenes = {os.path.basename(p): open(p, encoding="utf-8", errors="replace").read() for p in glob.glob(os.path.join(scene_dir, "*.scene"))}
    if outdir:
        for p in glob.glob(str(outdir / "*.scene")):
            scenes[os.path.basename(p)] = open(p, encoding="utf-8", errors="replace").read()
    code = am.code_sites(src, ids)
    sc = {c: sorted(n for n, body in scenes.items() if re.search(r"\b" + re.escape(c) + r"\b", body)) for c in ids}
    mh = {c: [] for c in ids}
    for mid, desc in re.findall(r'dict\(id="(M\d+)",\s*desc="([^"]*)"', mut):
        for c in ids:
            if re.search(r"\b" + re.escape(c) + r"\b", desc):
                mh[c].append(mid)
    out = {}
    for c in ids:
        hc, hs = bool(code[c]), bool(sc[c])
        out[c] = dict(light="ok" if hc and hs else "partial" if hc or hs else "none",
                      functions=sorted({f for f, _ in code[c]}), scenes=sc[c], mutants=sorted(mh[c]))
    return out


base = trace("")
for tree in ("299", "316", "all"):
    t = trace(tree)
    print("=== tree", tree)
    for c in ids:
        b, a = base[c], t[c]
        diffs = []
        if b["light"] != a["light"]:
            diffs.append("LIGHT %s->%s" % (b["light"], a["light"]))
        if b["functions"] != a["functions"]:
            diffs.append("functions -%s +%s" % (sorted(set(b["functions"]) - set(a["functions"])), sorted(set(a["functions"]) - set(b["functions"]))))
        if b["scenes"] != a["scenes"]:
            diffs.append("scenes +%s" % sorted(set(a["scenes"]) - set(b["scenes"])))
        if b["mutants"] != a["mutants"]:
            diffs.append("mutants +%s" % sorted(set(a["mutants"]) - set(b["mutants"])))
        if diffs:
            print(" ", c, "; ".join(diffs))
