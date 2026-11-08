"""Produce untouched R17-previous-main packages with the fixed producer."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys

PRODUCER = "343a8abe83029dd883e5e5b1b8e3112411fefe81"
root, out = map(lambda x: Path(x).resolve(), sys.argv[1:3])
assert subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip() == PRODUCER
subprocess.run(["git", "-C", str(root), "diff", "--exit-code", "HEAD", "--"], check=True)
out.mkdir(parents=True, exist_ok=False)
sys.path[:0] = [str(root), str(root / "geometry-core")]
os.environ.pop("GEOMETRY_MODEL_BASE", None)
from modeling import AXIOM_REVISION, AXIOM_SHA256, build_package, verify_package
from modeling.base import _build_adapter
from modeling.common import canonical_bytes
from tests.test_section_profile_modeling import scene, request
from tests.test_engineering_model_compatibility import EngineeringModelCompatibility, StaggerModelCompatibility

expected_pair = ("0fd8cacf799ed6ddf0fa7588243aa4e4bbb94c18", "c66c48e50e0caceef42721c79700365f090f5c48d297abba41993eeb40dba9b7")
assert (AXIOM_REVISION, AXIOM_SHA256) == expected_pair
assert hashlib.sha256((root / "公理層.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest() == AXIOM_SHA256
adapter = Path(_build_adapter()).resolve()
os.environ["GEOMETRY_MODEL_BASE"] = str(adapter)
inputs = {
    "profile": lambda: build_package({"base_scene": scene(), "extensions": []}, request()),
    "stagger": lambda: StaggerModelCompatibility().build(),
    "card": lambda: EngineeringModelCompatibility().card_reference_package(),
}
records = {}
for name, make in inputs.items():
    package = make()
    before = deepcopy(package)
    rebuilt = verify_package(package)
    assert package == before, name + ": verifier mutated input"
    assert rebuilt == package, name + ": own-version whole-package replay differs"
    data = canonical_bytes(package)
    path = out / (name + ".json")
    path.write_bytes(data)
    records[name] = {"file": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                     "capabilities": package["manifest"]["capabilities"], "sameVersionReplay": "whole package equal"}
    print(name, len(data), records[name]["sha256"], flush=True)
subprocess.run(["git", "-C", str(root), "diff", "--exit-code", "HEAD", "--"], check=True)
receipt = {"producerCommit": PRODUCER, "axiomRevision": AXIOM_REVISION, "axiomSha256LF": AXIOM_SHA256,
           "platform": platform.platform(), "python": platform.python_version(),
           "compiler": subprocess.check_output(["cc", "--version"], text=True).splitlines()[0],
           "stackLimitBytes": resource.getrlimit(resource.RLIMIT_STACK)[0],
           "adapterSha256": hashlib.sha256(adapter.read_bytes()).hexdigest(), "fixtures": records}
(out / "producer-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print("producer verify: all checks passed", flush=True)
