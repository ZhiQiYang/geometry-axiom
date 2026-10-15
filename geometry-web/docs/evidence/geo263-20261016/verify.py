"""Real native bridge: fixed / remove stagger serialization / restored.

Only a temporary frontend copy changes; compiler and native sources are not
mutated. Baseline failure is fatal, and errors/skips cannot count as killed.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FILES = ["grid-inspector.js", "grid-system-workspace.js", "grid_inspector_stagger_test.cjs"]


def main():
    original = (ROOT / "grid-inspector.js").read_bytes()
    needle = b"const stagger=d.parameterRefs?.stagger||d.stagger!=null?` stagger ${token('stagger')}`:'';"
    assert original.count(needle) == 1, "mutation target must be unique"
    receipt = {}
    with tempfile.TemporaryDirectory(prefix="geometry-263-mutant-") as folder:
        copy = Path(folder)
        for file in FILES:
            shutil.copyfile(ROOT / file, copy / file)
        for phase, data in (("fixed", original), ("mutant", original.replace(needle, b"const stagger='';")),
                            ("restored", original)):
            (copy / "grid-inspector.js").write_bytes(data)
            env = dict(os.environ, GEOMETRY_263_TRANSCRIPT=str(OUT / (phase + ".jsonl")))
            started = time.monotonic()
            result = subprocess.run(["node", str(copy / FILES[2])], env=env, capture_output=True, timeout=60)
            (OUT / (phase + ".stdout")).write_bytes(result.stdout)
            (OUT / (phase + ".stderr")).write_bytes(result.stderr)
            receipt[phase] = {"actual_exit": result.returncode, "seconds": time.monotonic() - started,
                              "inspector_sha256": hashlib.sha256(data).hexdigest(),
                              "test_sha256": hashlib.sha256((copy / FILES[2]).read_bytes()).hexdigest()}
            print(phase, "exit", result.returncode)
        assert (ROOT / FILES[0]).read_bytes() == original
    binary = Path(os.environ["GEOMETRY_TEST_BRIDGE"])
    receipt["bridge_sha256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
    (OUT / "mutation-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    for phase in ("fixed", "restored"):
        assert receipt[phase]["actual_exit"] == 0
        assert b"11 pass / 0 fail" in (OUT / (phase + ".stdout")).read_bytes()
    assert receipt["mutant"]["actual_exit"] == 1
    assert b"GEO263_STAGGER_LOST:" in (OUT / "mutant.stderr").read_bytes()
    assert len({receipt[p]["test_sha256"] for p in ("fixed", "mutant", "restored")}) == 1
    print("PASS: real bridge; stagger omission caught; same oracle; source restored")


if __name__ == "__main__":
    main()
