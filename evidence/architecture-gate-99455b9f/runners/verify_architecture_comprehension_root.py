"""Independent two-version reproduction of the reported scanner false greens."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

VERSIONS = {
    "before": "70ccab62d4fb3d3aba4dbac919f19ad3e4f8a7c8",
    "after": "99455b9f73c4175c1154f7e7be514204019930b8",
}
CASES = {
    "unpack": 'import sys\nalias, = [x for x in [sys]]\nmodule = alias.modules["w.policy"]\n',
    "indexed": 'import sys\nbox = [x for x in [sys]]\nmodule = box[0].modules["w.policy"]\n',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    REPO, OUT = options.repo.resolve(), options.out.resolve()
    OUT.mkdir(exist_ok=True)
    receipt = {"schema": "geo261-independent-scanner-regression/1", "cases": CASES, "versions": {}}
    with tempfile.TemporaryDirectory(prefix="geo261-root-comprehension-") as directory:
        temporary = Path(directory)
        for label, sha in VERSIONS.items():
            raw = subprocess.check_output(["git", "show", sha + ":tests/architecture_contract.py"], cwd=REPO)
            module_path = temporary / (label + ".py")
            module_path.write_bytes(raw)
            name = "geo261_architecture_" + label
            spec = importlib.util.spec_from_file_location(name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            outputs = {}
            for case, source in CASES.items():
                root = temporary / label / case
                files = {
                    "src/k/core.py": (source, "K"),
                    "src/w/__init__.py": ("", "W"),
                    "src/w/policy.py": ("VALUE = 1\n", "W"),
                    "src/h/app.py": ("import w.policy\n", "H"),
                }
                for path, (text, _) in files.items():
                    target = root / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(text, encoding="utf-8")
                manifest = {
                    "schema": "geometry-architecture/1", "sourceRoots": ["src"],
                    "searchRoots": {"c": ["src"], "python": ["src"], "javascript": ["src"]},
                    "sources": [{"path": path, "layer": layer, "language": "python", "purpose": "Independent reported comprehension regression"}
                                for path, (_, layer) in files.items()],
                    "exclusions": [],
                    "policy": {"cSystemHeaders": [], "pythonStdlib": ["sys"], "javascriptBuiltins": [],
                               "externalModules": [], "forbiddenIdentifiers": [], "forbiddenStrings": [],
                               "forbiddenModules": {"c": [], "python": [], "javascript": []}},
                }
                result = module.scan(root, manifest)
                outputs[case] = result.to_dict()
                if label == "before":
                    assert result.ok and not result.diagnostics, outputs[case]
                else:
                    assert not result.ok, outputs[case]
                    assert any(d.code == "CORE_PATH_INJECTION" and d.path == "src/k/core.py" for d in result.diagnostics), outputs[case]
            receipt["versions"][label] = {"sha": sha, "scannerSha256": hashlib.sha256(raw).hexdigest(), "results": outputs}
        suite_dir = temporary / "frozen-suite"
        suite_dir.mkdir()
        suite_inputs = {}
        for filename in ("architecture_contract.py", "test_architecture_contract.py"):
            raw = subprocess.check_output(["git", "show", VERSIONS["after"] + ":tests/" + filename], cwd=REPO)
            (suite_dir / filename).write_bytes(raw)
            suite_inputs[filename] = hashlib.sha256(raw).hexdigest()
        run = subprocess.run([sys.executable, "-B", str(suite_dir / "test_architecture_contract.py")],
                             cwd=suite_dir, capture_output=True, timeout=120)
        raw_log = run.stdout + run.stderr
        (OUT / "frozen-205.log").write_bytes(raw_log)
        text = raw_log.decode("utf-8", "replace")
        count = re.search(r"Ran (\d+) tests", text)
        assert run.returncode == 0 and count and count[1] == "205", text
        receipt["frozenSuite"] = {"source": VERSIONS["after"], "inputs": suite_inputs,
                                  "exit": run.returncode, "testsRun": int(count[1]),
                                  "skips": 1 if "OK (skipped=1)" in text else 0,
                                  "logSha256": hashlib.sha256(raw_log).hexdigest()}
    receipt["temporaryRemoved"] = not Path(directory).exists()
    receipt["runnerSha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    receipt["result"] = "Both original false greens reproduced; both fixed sources explicitly rejected. No product manifest or product execution."
    (OUT / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "oldFalseGreens": 2, "newExplicitRejections": 2, "receipt": str(OUT / "receipt.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
