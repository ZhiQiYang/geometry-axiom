"""Named L12 behavioral controls using actual Python product source in memory.

Does not modify product files or the native mutation ledger. Native children
still pass their normal fresh-binary checks. The stale-route case retains the
controlled pipe fixture explicitly documented in the underlying test.
"""
from contextlib import ExitStack
import importlib.machinery
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(sys.argv[1]).resolve()
MUTANT = sys.argv[2]
sys.path.insert(0, str(ROOT))
from tests import test_identity_content_contract as contract

ROWS = {
    "L12-NATIVE-CAPABILITY": (
        "test_L12_bridge_and_model_capability_gates_are_distinct",
        "L12_MODEL_CAPABILITY_MUST_NOT_BE_WIDENED"),
    "L12-MODEL-DEFAULT": (
        "test_L12_bridge_and_model_capability_gates_are_distinct",
        "ModelError not raised"),
    "L12-RULE-CASE-FULL": (
        "test_L12_rule_case_hashes_use_deidentified_dump_in_an_actual_active_child",
        "L12_RULE_CASE_DEIDENTIFIED_COMMAND"),
    "L12-STALE-DUMP": (
        "test_L12_stale_host_allows_deidentified_read_and_blocks_new_writes",
        "L12_STALE_HOST_MUST_ALLOW_DEIDENTIFIED_DUMP"),
}
method, marker = ROWS[MUTANT]

def replace_source(text, old, new, count=1):
    assert text.count(old) == count, (MUTANT, "anchor count", text.count(old), count)
    return text.replace(old, new)

def execute_variant(module, old, new, count=1):
    filename = Path(module.__file__)
    text = replace_source(filename.read_text(), old, new, count)
    exec(compile(text, str(filename), "exec"), module.__dict__)

with ExitStack() as stack:
    if MUTANT == "L12-NATIVE-CAPABILITY":
        execute_variant(contract.scenario_verify,
                        'NATIVE_CAPABILITIES = frozenset(("engineering-spec/1",',
                        'NATIVE_CAPABILITIES = frozenset(("identity-ledger/1", "engineering-spec/1",')
    elif MUTANT == "L12-MODEL-DEFAULT":
        execute_variant(contract.scenario_verify,
                        'def _capabilities(value, path, *, supported=NATIVE_CAPABILITIES):',
                        'def _capabilities(value, path, *, supported=BRIDGE_CAPABILITIES):')
    elif MUTANT == "L12-RULE-CASE-FULL":
        execute_variant(contract.executor, 'command("dump-deidentified")["text"]',
                        'command("dump")["text"]', 2)
    elif MUTANT == "L12-STALE-DUMP":
        original = importlib.machinery.SourceFileLoader.get_code
        serve = ROOT / "geometry-web/serve.py"
        def get_code(loader, fullname):
            if Path(loader.path).resolve() == serve:
                text = replace_source(serve.read_text(),
                    "{'dump', 'dump-deidentified', 'identity-read', 'objects',",
                    "{'dump', 'identity-read', 'objects',")
                return compile(text, str(serve), "exec")
            return original(loader, fullname)
        stack.enter_context(patch.object(importlib.machinery.SourceFileLoader,
                                         "get_code", get_code))
    suite = unittest.TestSuite([contract.IdentityContentContract(method)])
    result = unittest.TextTestRunner(verbosity=2).run(suite)

assert result.testsRun == 1, (MUTANT, "wrong test count")
assert not result.errors, (MUTANT, "tool/import/runtime error is not killed", result.errors)
assert len(result.failures) == 1 and marker in result.failures[0][1], (
    MUTANT, "required exact assertion did not kill", result.failures)
print(json.dumps({"id": MUTANT, "testsRun": result.testsRun,
                  "status": "killed-by-named-assertion", "marker": marker,
                  "errors": 0, "productFilesChanged": False}))
