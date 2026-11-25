#!/usr/bin/env python3
"""Named browser withdrawal for PR #448 U123-H:A narrow workspace strip.

The shared runner owns checkout, Chrome, exact source restoration and 0/1/0
classification. This wrapper supplies one exact CSS withdrawal and its named
assertion; it does not relax a timeout or rewrite browser output.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "diagnostics"))
import r16_height_mutations as runner

runner.BASE_SHA = "b28c330f2e39d041363266e9789ccc492a76d169"

BEGIN = "/* R123H_NARROW_WORKSPACE_STRIP_BEGIN:"
END = "/* R123H_NARROW_WORKSPACE_STRIP_END */"


def definitions(root):
    relative = "geometry-web/workspace-height.css"
    path = root / relative
    source = path.read_bytes()
    if b"\r" in source:
        raise ValueError("R123H narrow-strip mutation requires the LF Linux checkout")
    text = source.decode("utf-8")
    start = text.index(BEGIN)
    finish = text.index(END, start) + len(END)
    before = text[start:finish]
    after = "/* R123H_NARROW_WORKSPACE_STRIP_WITHDRAWN */"
    changed = source.replace(before.encode("utf-8"), after.encode("utf-8"), 1)
    return [{
        "id": "R123H_FACE_HELP_NARROW_STRIP_REVERT",
        "case": runner.CASE,
        "assertions": ["R123H_FACE_HELP_REACH"],
        "meaning": "561px returns to the asymmetric three-column lane; the 74px face help is clipped by the 33px tools viewport",
        "changes": [{"file": relative, "before": before, "after": after}],
        "beforeBytes": len(source),
        "beforeSha256": runner.sha(source),
        "afterBytes": len(changed),
        "afterSha256": runner.sha(changed),
    }]


_original_manifest_for = runner.manifest_for


def manifest_for(root, mutations):
    manifest = _original_manifest_for(root, mutations)
    manifest["suite"] = "r16-u123h-face-help-narrow-strip"
    additions = [
        Path(__file__).resolve().relative_to(root).as_posix(),
        "tests/diagnostics/r123h_matrix_probe.cjs",
        "tests/diagnostics/r123h_length_paint_probe.cjs",
    ]
    for item in additions:
        if item not in manifest["inputs"]:
            manifest["inputs"].append(item)
    manifest["inputs"] = sorted(manifest["inputs"])
    return manifest


runner.definitions = definitions
runner.manifest_for = manifest_for

if __name__ == "__main__":
    raise SystemExit(runner.main())
