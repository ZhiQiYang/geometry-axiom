# -*- coding: utf-8 -*-
"""Tiny helpers: an in-memory file tree over the 09ab5f79 base files and a git-style unified diff writer.

No repository file is touched; everything reads from scratchpad/work/base and writes to scratchpad/work/out*.
"""
import difflib
import pathlib

WORK = pathlib.Path(__file__).resolve().parent
BASE = WORK / "base"


def decode(data: bytes) -> str:
    return data.decode("utf-8", "surrogateescape")


def encode(text: str) -> bytes:
    return text.encode("utf-8", "surrogateescape")


class Tree:
    def __init__(self):
        self.files = {}      # path -> text (existing files, possibly modified)
        self.added = {}      # path -> text (new files)

    def get(self, path):
        if path in self.added:
            return self.added[path]
        if path not in self.files:
            self.files[path] = decode((BASE / path).read_bytes())
        return self.files[path]

    def put(self, path, text):
        if path in self.added:
            self.added[path] = text
        else:
            self.get(path)
            self.files[path] = text

    def sub(self, path, old, new, count=1):
        text = self.get(path)
        n = text.count(old)
        assert n == count, (path, old[:100], n)
        self.put(path, text.replace(old, new))

    def add(self, path, text):
        assert path not in self.added and not (BASE / path).exists()
        self.added[path] = text

    def changed(self):
        """[(path, old_text_or_None, new_text)] for every modified or added file."""
        out = []
        for path in sorted(self.files):
            old = decode((BASE / path).read_bytes())
            if self.files[path] != old:
                out.append((path, old, self.files[path]))
        for path in sorted(self.added):
            out.append((path, None, self.added[path]))
        return out


def to_lines(text):
    parts = text.split("\n")
    lines = [p + "\n" for p in parts[:-1]]
    assert parts[-1] == "", "file must end with a newline"
    return lines


def group_opcodes(codes, n=3):
    codes = list(codes)
    if not codes:
        codes = [("equal", 0, 1, 0, 1)]
    if codes[0][0] == "equal":
        tag, i1, i2, j1, j2 = codes[0]
        codes[0] = tag, max(i1, i2 - n), i2, max(j1, j2 - n), j2
    if codes[-1][0] == "equal":
        tag, i1, i2, j1, j2 = codes[-1]
        codes[-1] = tag, i1, min(i2, i1 + n), j1, min(j2, j1 + n)
    nn = n + n
    group = []
    for tag, i1, i2, j1, j2 in codes:
        if tag == "equal" and i2 - i1 > nn:
            group.append((tag, i1, min(i2, i1 + n), j1, min(j2, j1 + n)))
            yield group
            group = []
            i1, j1 = max(i1, i2 - n), max(j1, j2 - n)
        group.append((tag, i1, i2, j1, j2))
    if group and not (len(group) == 1 and group[0][0] == "equal"):
        yield group


def fmt_range(start, stop):
    length = stop - start
    beginning = start + 1
    if length == 1:
        return str(beginning)
    if not length:
        beginning -= 1
    return "%d,%d" % (beginning, length)


def diff_one(path, old, new):
    a = to_lines(old) if old is not None else []
    b = to_lines(new)
    # Trim common prefix/suffix so SequenceMatcher only sees the edited middle.
    p = 0
    while p < len(a) and p < len(b) and a[p] == b[p]:
        p += 1
    s = 0
    while s < len(a) - p and s < len(b) - p and a[len(a) - 1 - s] == b[len(b) - 1 - s]:
        s += 1
    ma, mb = a[p:len(a) - s], b[p:len(b) - s]
    codes = []
    if p:
        codes.append(("equal", 0, p, 0, p))
    sm = difflib.SequenceMatcher(None, ma, mb, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        codes.append((tag, i1 + p, i2 + p, j1 + p, j2 + p))
    if s:
        codes.append(("equal", len(a) - s, len(a), len(b) - s, len(b)))
    out = ["diff --git a/%s b/%s\n" % (path, path)]
    if old is None:
        out.append("new file mode 100644\n--- /dev/null\n")
    else:
        out.append("--- a/%s\n" % path)
    out.append("+++ b/%s\n" % path)
    for group in group_opcodes(codes, 3):
        first, last = group[0], group[-1]
        out.append("@@ -%s +%s @@\n" % (fmt_range(first[1], last[2]), fmt_range(first[3], last[4])))
        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                out.extend(" " + line for line in a[i1:i2])
                continue
            if tag in ("replace", "delete"):
                out.extend("-" + line for line in a[i1:i2])
            if tag in ("replace", "insert"):
                out.extend("+" + line for line in b[j1:j2])
    return "".join(out)


def make_patch(tree):
    return encode("".join(diff_one(path, old, new) for path, old, new in tree.changed()))


def write_tree(tree, outdir):
    outdir = pathlib.Path(outdir)
    for path, old, new in tree.changed():
        target = outdir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(encode(new))
