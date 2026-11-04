"""R365 owner/R57/typed-selection mutations; source and behavioral oracle pinned.

The normal suite validates live anchors. --run executes the real Node adapters
against one isolated mutated file at a time and requires baseline/red/restored.
It never writes a historical mutation receipt or changes repository sources.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LINKS = "geometry-web/evidence-links.js"
APP = "geometry-web/evidence-links-app.js"
TESTS = ["tests/test_evidence_owner_contract.cjs", "tests/test_evidence_app_contract.cjs"]
MUTATIONS = [
    ("R365_OWNER_AFTER_ACTIVATION", LINKS,
     "guardOwner();const s=stamp();", "const s=stamp();", 2,
     "R365_NO_TARGET_READ_IN_REPLACEMENT"),
    ("R365_CONTINUOUS_TARGET_BINDING", LINKS,
     "if(!targetValidV2({...current.target,identityBasis:'ledger'})||targetKey(current.target)!==targetKey(link.target)||current.target.incarnation!==link.target.incarnation)",
     "if(false)", 1, "R365_CONTINUITY_REQUIRES_SAME_TARGET"),
    ("R365_NATIVE_ACTIVE_GATE", LINKS,
     "graph.data.identityLedger?.active!==true||", "", 1,
     "R365_INACTIVE_IS_UNKNOWN"),
    ("R365_CROSS_KEY_CONFLICT", LINKS,
     "for(const node of graph.nodes.values())if(node.incarnation===target.incarnation&&node.key!==key)return 'conflict';", "", 1,
     "R365_CONFLICT_BEFORE_ABSENT"),
    ("R365_ACTIVATION_WRITE_OWNER", APP,
     "const read=await apiRequest('identity-read');\n            assertCurrent();\n            if(!current(initial))throw Error('讀取身分帳期間專案已變更，未啟用。');",
     "const read=await apiRequest('identity-read');", 1,
     "R365_ACTIVATION_BEFORE_NATIVE_WRITE"),
    ("R365_SELECTED_OBJECT_TARGETS", APP,
     ").concat(objectTargets)};", ")};", 1,
     "R365_BOUNDARY_CARD_TARGET"),
]


def check():
    problems = []
    oracles = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in TESTS)
    for name, path, before, _after, count, marker in MUTATIONS:
        actual = (ROOT / path).read_text(encoding="utf-8").count(before)
        if actual != count:
            problems.append(f"{name}: anchor count {actual} != {count}")
        if marker not in oracles:
            problems.append(f"{name}: named behavioral oracle missing: {marker}")
    return problems


class EvidenceContractMutationRegistry(unittest.TestCase):
    def test_live_anchors_and_named_behavior_oracles(self):
        self.assertEqual(check(), [], "R365_MUTATION_REGISTRY")


def run_mutations(destination):
    problems = check()
    if problems:
        raise AssertionError(problems)
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    command = ["node", "--test", *TESTS]
    def execute(label, env):
        result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=60)
        (out / (label + ".log")).write_text(result.stdout, encoding="utf-8", newline="\n")
        return result
    baseline = execute("baseline", os.environ.copy())
    if baseline.returncode:
        raise AssertionError("R365 baseline must pass before mutation")
    receipts = []
    with tempfile.TemporaryDirectory(prefix="r365-contract-mutants-") as temp:
        for name, path, before, after, count, marker in MUTATIONS:
            original = (ROOT / path).read_text(encoding="utf-8")
            mutated = original.replace(before, after)
            target = Path(temp) / Path(path).name
            target.write_text(mutated, encoding="utf-8", newline="\n")
            env = os.environ.copy()
            env["EVIDENCE_LINKS_MODULE" if path == LINKS else "EVIDENCE_APP_MODULE"] = str(target)
            result = execute(name, env)
            if result.returncode == 0 or marker not in result.stdout or "AssertionError" not in result.stdout:
                raise AssertionError(f"{name}: not killed by named assertion {marker}")
            restored = execute(name + "-restored", os.environ.copy())
            if restored.returncode:
                raise AssertionError(f"{name}: restored product is not green")
            receipts.append({"name": name, "source": path, "oracle": marker,
                             "sourceSha256": hashlib.sha256(original.encode()).hexdigest(),
                             "mutatedSha256": hashlib.sha256(mutated.encode()).hexdigest(),
                             "before": 0, "mutated": result.returncode, "restored": 0})
    (out / "receipts.json").write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"mutations": len(receipts), "killed": len(receipts), "baseline": 0, "restored": 0}))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--run":
        run_mutations(sys.argv[2])
    else:
        unittest.main()
