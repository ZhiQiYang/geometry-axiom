# -*- coding: utf-8 -*-
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import Tree, make_patch, write_tree, WORK
import edits299
import edits316

trees = {
    "299": edits299.e299(Tree()),
    "316": edits316.e316(Tree()),
    "all": edits316.e316(edits299.e299(Tree())),
}
for name, tree in trees.items():
    out = WORK / ("out" + name)
    if out.exists():
        shutil.rmtree(out)
    write_tree(tree, out)
    patch = make_patch(tree)
    (WORK / ("patch" + name + ".diff")).write_bytes(patch)
    print(name, "files:", [p for p, _, _ in tree.changed()], "patch bytes:", len(patch))
