"""Contract tests for the evidence entry points, without launching CI jobs."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


def job(text, name):
    match = re.search(r"(?m)^  " + re.escape(name) + r":\n", text)
    if match is None:
        return ""
    following = re.search(r"(?m)^  [a-z][a-z0-9-]*:\n", text[match.end():])
    return text[match.start():match.end() + following.start()] if following else text[match.start():]


class EvidenceWorkflowTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")

    def test_architecture_refresh_does_not_dispatch_mutants(self):
        path = ROOT / ".github/workflows/architecture-evidence.yml"
        self.assertTrue(path.is_file(), "architecture-only refresh needs an independent official CI entry point")
        text = path.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("timeout-minutes: 15", job(text, "architecture"))
        self.assertIn("python3 -B .github/scripts/architecture_evidence.py --out", text)
        self.assertIn("python3 -B .github/scripts/evidence_architecture.py import", text)
        self.assertNotIn("mutation_evidence.py", text)
        self.assertNotIn("tests/mutate.py", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("contents: read", text)

    def test_full_mutation_workflow_keeps_original_execution_and_packages_architecture(self):
        text = self.read("mutation-evidence.yml")
        architecture = job(text, "architecture")
        self.assertIn(".github/scripts/evidence_architecture.py import", architecture,
                      "full ME must publish the same immutable architecture format as the independent route")
        self.assertLess(architecture.index("architecture_evidence.py --out"),
                        architecture.index("evidence_architecture.py import"))
        self.assertIn(".github/scripts/mutation_evidence.py run", job(text, "execute"))
        self.assertIn("timeout-minutes: 45", job(text, "execute"))
        self.assertIn(".github/scripts/mutation_evidence.py verify", job(text, "verify"))
        self.assertIn("timeout-minutes: 10", job(text, "verify"))

    def test_native_materializes_before_original_pinned_ledger_check(self):
        text = self.read("integration-tests.yml")
        native = job(text, "native")
        command = "python3 -B .github/scripts/evidence_records.py materialize"
        self.assertIn(command, native,
                      "run_all pins tests/mutants_results.json; it must read the checked repo store view")
        self.assertLess(native.index(command), native.index("python3 tests/run_all.py --build"))
        self.assertIn("timeout-minutes: 35", native)
        self.assertIn("shard: [1, 2, 3, 4, 5, 6]", native)
        self.assertNotIn("MUTATE_RESULTS", native)
        self.assertIn("timeout-minutes: 5", job(text, "native-complete"))

    def test_repo_store_is_a_required_unconditional_check(self):
        text = self.read("integration-tests.yml")
        evidence = job(text, "evidence-store")
        self.assertTrue(evidence, "stored current-source evidence must have its own CI gate")
        self.assertNotRegex(evidence, r"(?m)^    if:")
        self.assertNotIn("continue-on-error", evidence)
        for test in ("test_evidence_records.py", "test_evidence_architecture.py", "test_evidence_workflow.py"):
            self.assertIn("python3 -B .github/scripts/" + test, evidence)
        self.assertIn("python3 -B .github/scripts/evidence_records.py check", evidence)
        self.assertIn("python3 -B .github/scripts/evidence_architecture.py check", evidence)
        self.assertIn("timeout-minutes: 5", evidence)

    def test_evidence_bytes_survive_an_autocrlf_checkout(self):
        paths = (
            ".github/evidence/mutations/objects/fixture.json",
            ".github/evidence/architecture/key/receipt/architecture-unit.stderr",
            "tests/mutants_results.json",
            "geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md",
            "geometry-core/domain-decoupling/product-architecture-receipt.json",
            "geometry-core/domain-decoupling/product-architecture-scan.json",
        )
        raw = b"original evidence bytes\nsecond line\n"
        with tempfile.TemporaryDirectory(prefix="r214-checkout-bytes-") as temporary:
            root = Path(temporary)
            (root / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
            for relative in (*paths, "unprotected-control.txt"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            commands = (("init", "-q"), ("add", "-A"),
                        ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                         "commit", "-qm", "original raw fixture"))
            for command in commands:
                subprocess.run(["git", "-c", "core.autocrlf=false", *command], cwd=root,
                               check=True, capture_output=True)
            for relative in (*paths, "unprotected-control.txt"):
                (root / relative).unlink()
            subprocess.run(["git", "-c", "core.autocrlf=true", "checkout", "--force", "HEAD", "--", "."],
                           cwd=root, check=True, capture_output=True)
            self.assertEqual((root / "unprotected-control.txt").read_bytes(), raw.replace(b"\n", b"\r\n"))
            for relative in paths:
                with self.subTest(path=relative):
                    self.assertEqual((root / relative).read_bytes(), raw,
                                     "checkout must preserve the bytes committed by the evidence producer")


if __name__ == "__main__":
    unittest.main(verbosity=2)
