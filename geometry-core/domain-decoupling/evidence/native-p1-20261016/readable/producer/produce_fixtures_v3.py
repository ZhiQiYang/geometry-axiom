"""Freeze genuine a898ad6e outputs; never rewrites a saved package manifest.

Run with the fixed baseline checkout and its own compiled adapter. The output
directory must be new. Source subdivision is intentionally a rejected input:
the baseline model executor does not implement grid-subdivision-rules/1.
"""
from copy import deepcopy
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys

PRODUCER = "a898ad6e12707104568679591fe1b21804bfc3df"
VERSION = ("b3c79615d0cde89bbdca72c1223d214324bc5f8f",
           "e5e43ec5da2030669c9ecd7a67f8b250cfb7290cf663365b2b66c51814bb77b9")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root, adapter, out = args.root.resolve(), args.base.resolve(), args.out.resolve()
    if out.exists():
        raise SystemExit("Output exists; preserve it and choose a fresh evidence directory")
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "geometry-core"))
    import modeling
    from modeling.common import canonical_bytes
    from tests.test_section_profile_modeling import scene as profile_scene, request as profile_request
    from tests.test_engineering_model_compatibility import StaggerModelCompatibility
    assert (modeling.AXIOM_REVISION, modeling.AXIOM_SHA256) == VERSION
    assert modeling._axiom_hash() == VERSION[1]
    assert Path(modeling.__file__).resolve().is_relative_to(root)
    assert not hasattr(modeling, "PRE_DECOUPLING_AXIOM_VERSIONS")
    case = json.loads((root / "geometry-core/modeling-cases.json").read_bytes())["cases"][0]
    cases = {}
    cases["profile"] = {"definitions": {"base_scene": profile_scene(), "extensions": []},
                        "request": profile_request()}
    finite = deepcopy({k: case[k] for k in ("definitions", "request")})
    finite["definitions"]["base_scene"] += (
        "grid-system 0 name-hex e585b1e794a8 main-along none u series 100 100 3 v none\n"
        "grid 0 on 1 from-system 0 origin 0 0\n")
    cases["finite-grid"] = finite
    infinite = deepcopy({k: case[k] for k in ("definitions", "request")})
    infinite["definitions"]["base_scene"] += (
        "boundary-vertex-keys 1 outer 1 2 3 4 hole 5 6 7 8 next-key 9\n"
        "grid-system 0 name-hex e784a1e99990 main-along none u repeat 0 600 v repeat 0 400\n"
        "grid-binding 0 on-boundary 1 from-system 0 vertex-key 1 cell -2 1 anchor 1 2 1 2\n"
        "grid 0 on 1 from-binding 0\n")
    cases["infinite-grid"] = infinite
    stagger = StaggerModelCompatibility()
    cases["stagger"] = {"definitions": stagger.definitions(stagger.scene(band=-1)),
                        "request": stagger.request()}
    def parameter_record(kind, value):
        return "parameters " + kind + " " + base64.b64encode(canonical_bytes(value)).decode() + "\n"
    parameters = ("requires parameters/1\nparameters begin\n" +
                  parameter_record("card", {"id": 1, "name": "Pitch", "nextFieldId": 2}) +
                  parameter_record("field", {"parameterId": 1, "id": 1, "name": "v-pitch", "type": 0,
                                             "expression": {"op": "literal", "num": "1830", "den": "1", "unit": "mm"}}) +
                  "parameters end\n")
    source = parameters + stagger.scene(None).replace("v repeat 0 1830", "v repeat 0 param:1:1")
    cases["parameter"] = {"definitions": stagger.definitions(source), "request": stagger.request()}
    rejected = deepcopy(infinite)
    rejected["definitions"]["base_scene"] += (
        "requires grid-subdivision-rules/1\n"
        "grid-source-rule 0 key 1 name-hex 72 selector all-cells divide 3 2\n"
        "grid-source-rule-highwater 0 next 2\n")
    out.mkdir(parents=True)
    evidence = {"producer_commit": PRODUCER, "axiom_version": list(VERSION),
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "adapter_sha256": hashlib.sha256(adapter.read_bytes()).hexdigest(),
                "source_sha256": {}, "fixtures": {}}
    for relative in ("geometry-core/modeling/__init__.py", "geometry-core/model_base.c",
                     "geometry-core/modeling/base.py", "geometry-core/modeling/engine.py",
                     "tests/test_section_profile_modeling.py", "tests/test_engineering_model_compatibility.py",
                     "geometry-core/modeling-cases.json"):
        evidence["source_sha256"][relative] = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    def save(name, value):
        raw = canonical_bytes(value)
        (out / name).write_bytes(raw)
        evidence["fixtures"][name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    for name, value in cases.items():
        source = deepcopy(value)
        package = modeling.build_package(**value, base_executable=str(adapter))
        assert value == source, name + ": producer altered input"
        assert modeling.verify_package(package, base_executable=str(adapter)) == package
        assert (package["manifest"]["axiom_revision"], package["manifest"]["axiom_sha256"]) == VERSION
        save(name + ".input.json", value)
        save(name + ".json", package)
        print(name + ": genuine baseline build + verify passed", flush=True)
    try:
        modeling.build_package(**rejected, base_executable=str(adapter))
    except modeling.ModelError as exc:
        assert (exc.status, exc.code, exc.clause) == ("UNSUPPORTED", "CAPABILITY", "I32")
        save("subdivision-rejected.json", {"input": rejected, "expected": exc.as_dict()})
        print("subdivision: genuine baseline UNSUPPORTED/CAPABILITY/I32", flush=True)
    else:
        raise AssertionError("Baseline must not pretend to support subdivision model sources")
    save("historical-versions.json", {
        name: sorted(value) for name, value in vars(modeling).items()
        if name.endswith("_AXIOM_VERSIONS") and isinstance(value, frozenset)})
    save("model-contract.json", {"schema": modeling.SCHEMA, "profile": modeling.PROFILE,
                                 "generator": modeling.GENERATOR,
                                 "capabilities": list(modeling.CAPABILITIES)})
    (out / "producer-receipt.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
