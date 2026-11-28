#!/usr/bin/env python3
"""Counterfactual corruption probes over freshly generated native artifacts.

Only negative inputs are edited. No modified file is called native output.
The expected failure must be the typed-root guard itself, not a later mismatch.
"""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-artifacts", type=Path, required=True)
    parser.add_argument("--projection", type=Path, default=Path(__file__).with_name("native_projection.py"))
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("u476_projection_probe", args.projection.resolve())
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = args.native_artifacts.resolve()
    count = 0
    for name in ("single", "independent-control"):
        original = root / name
        good = module.project(original)
        assert good["studySchema"] == "U476-facts/1"
        for filename in ("all-three", "live-graph.json", "snapshot.json", "package-snapshot.json"):
            for kind in ("timber", "placement"):
                for corruption in ("kind", "id", "noncanonical-id"):
                    with tempfile.TemporaryDirectory(prefix="u476-negative-root-") as temp:
                        target = Path(temp) / name
                        shutil.copytree(original, target)
                        shutil.copyfile(root / "cutting-settings.json", Path(temp) / "cutting-settings.json")
                        files = ("live-graph.json", "snapshot.json", "package-snapshot.json") if filename == "all-three" else (filename,)
                        for current in files:
                            path = target / current
                            graph = json.loads(path.read_text(encoding="utf-8"))
                            node = next(node for node in graph["nodes"] if node["key"] == kind + ":0")
                            if corruption == "kind":
                                node["kind"] = "boundary" if kind == "placement" else "guide"
                            elif corruption == "id":
                                node["id"] = "9"
                            else:
                                node["id"] = "00"
                            path.write_text(json.dumps(graph) + "\n", encoding="utf-8")
                        wanted = "U476_NATIVE_ROOT_ID_CANONICAL" if corruption == "noncanonical-id" else "U476_NATIVE_TYPED_ROOT_MISMATCH"
                        try:
                            module.project(target)
                        except AssertionError as error:
                            assert str(error) == wanted, ("U476_ROOT_GUARD_WRONG_FAILURE", name, filename, kind, corruption, str(error))
                        else:
                            raise AssertionError(("U476_ROOT_GUARD_ACCEPTED_CORRUPTION", name, filename, kind, corruption))
                    count += 1
    print(json.dumps({"ok": True, "researchOnly": True, "realBaselineScenarios": 2,
                      "negativeCounterfactuals": count, "expectedFailure": "typed root guard, not downstream content mismatch"}))


if __name__ == "__main__":
    main()
