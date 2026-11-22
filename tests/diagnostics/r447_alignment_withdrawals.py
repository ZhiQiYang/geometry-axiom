#!/usr/bin/env python3
"""Independent 0/1/0 source withdrawals for the PF-6 guard alignment.

The live checkout is never edited. Each phase compiles one repository test
module from its original or deliberately withdrawn source bytes in a fresh
process. Only the named existing assertion may produce mutant exit 1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
R14 = ROOT / "tests/test_r14_repeat_panel.py"
GEO261 = ROOT / "tests/test_geo261_mutation_migration.py"
for entry in (ROOT, ROOT / "tests"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

R14_EXPECTED = ('["section-profile-native/1", "panel-fill-native/1", '
                '"grid-subdivision-native/2", "panel-fill-builder-native/1"]')
R14_WRONG_POSITION = ('["section-profile-native/1", "panel-fill-native/1", '
                      '"panel-fill-builder-native/1", "grid-subdivision-native/2"]')
R14_REMOVE_LEGACY = ('["section-profile-native/1", "grid-subdivision-native/2", '
                     '"panel-fill-builder-native/1"]')
PF6_OWNER_ROW = ('            "PF6_UNSELECTED_CREATES": '
                 '"geometry-app/native/panel_fill_builder.inc",' + chr(10))

CASES = {
    "R447_PF6_OWNER_REGISTRATION_OMITTED": {
        "path": GEO261,
        "before": PF6_OWNER_ROW,
        "after": "",
        "assertion": "PF6_NATIVE_IDS_IN_DECLARATION_ORDER",
        "kind": "geo261",
    },
    "R447_PF6_CAPABILITY_WRONG_POSITION": {
        "path": R14,
        "before": R14_EXPECTED,
        "after": R14_WRONG_POSITION,
        "assertion": "R14_NATIVE_CAPABILITY_EXPLICIT_AND_ORDERED",
        "kind": "r14",
    },
    "R447_PF6_LEGACY_CAPABILITY_REMOVED": {
        "path": R14,
        "before": R14_EXPECTED,
        "after": R14_REMOVE_LEGACY,
        "assertion": "R14_NATIVE_CAPABILITY_EXPLICIT_AND_ORDERED",
        "kind": "r14",
    },
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(path: Path, before: str | None, after: str | None, name: str):
    raw = path.read_bytes()
    if 13 in raw:
        raise RuntimeError("R447_ALIGNMENT_SOURCE_NOT_LF: " + str(path))
    source = raw.decode("utf-8")
    if before is not None:
        if source.count(before) != 1:
            raise RuntimeError("R447_ALIGNMENT_EXACT_ANCHOR: " + str(path))
        source = source.replace(before, after, 1)
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = "tests"
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


class CapabilitiesAccepted(Exception):
    """The exact capability check passed and reached the next product action."""


def exercise_r14(module) -> None:
    method = "test_13_host_capability_includes_panel_rules_without_changing_native_identity"
    case = module.R14RepeatPanelNative(method)
    host = ["engineering-spec/1", "parameters/1", "assembly-rule-authoring/1",
            "assembly-timber-generation/1", "assembly-bay-repeat/1", "grid-subdivision-rules/1",
            "grid-subdivision-rules/2", "section-profile/1", "grid-card-reference/1",
            "identity-ledger/1", "definition-import/1"]
    native = ["section-profile-native/1", "panel-fill-native/1", "grid-subdivision-native/2",
              "panel-fill-builder-native/1"]

    def read(command):
        if command != "engineering-read":
            raise AssertionError("R447_ALIGNMENT_UNEXPECTED_COMMAND " + command)
        return {"state": {"capabilities": host, "native_capabilities": native}}

    with patch.object(case, "command", read), patch.object(case, "seed", side_effect=CapabilitiesAccepted):
        try:
            getattr(case, method)()
        except CapabilitiesAccepted:
            return
    raise AssertionError("R447_ALIGNMENT_R14_DID_NOT_REACH_SEED")


def exercise_geo261(module) -> None:
    method = "test_all_fifty_definitions_keep_live_or_retired_targets"
    case = module.LiveMutationAnchorMigration(method)
    getattr(case, method)()


def execute(identifier: str, phase: str) -> int:
    spec = CASES[identifier]
    withdrawn = phase == "mutant"
    try:
        module = load_module(
            spec["path"], spec["before"] if withdrawn else None,
            spec["after"] if withdrawn else None,
            "_r447_" + identifier.lower() + "_" + phase,
        )
        (exercise_r14 if spec["kind"] == "r14" else exercise_geo261)(module)
    except AssertionError as error:
        if withdrawn and spec["assertion"] in str(error):
            print(spec["assertion"], file=sys.stderr)
            return 1
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        return 2
    except Exception as error:  # setup/import/runtime failures never count as killed
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        return 2
    if withdrawn:
        print("R447_ALIGNMENT_WITHDRAWAL_SURVIVED " + identifier, file=sys.stderr)
        return 2
    return 0


def supervise() -> int:
    original = {path: path.read_bytes() for path in (R14, GEO261)}
    rows = []
    for identifier, spec in CASES.items():
        phases = []
        for phase in ("baseline", "mutant", "restored"):
            try:
                result = subprocess.run(
                    [sys.executable, "-B", __file__, "--case", identifier, "--phase", phase],
                    cwd=ROOT, text=True, encoding="utf-8", errors="replace",
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
                )
                phases.append({"phase": phase, "exit": result.returncode,
                               "stdout": result.stdout, "stderr": result.stderr})
            except subprocess.TimeoutExpired as error:
                phases.append({"phase": phase, "exit": 2,
                               "stdout": error.stdout or "",
                               "stderr": "R447_ALIGNMENT_PHASE_TIMEOUT"})
        exits = [row["exit"] for row in phases]
        restored = all(path.read_bytes() == data for path, data in original.items())
        rows.append({
            "id": identifier,
            "assertion": spec["assertion"],
            "baselineMutantRestoredExit": exits,
            "sourceRestoredExactly": restored,
            "source": str(spec["path"].relative_to(ROOT)),
            "sourceSha256": sha(original[spec["path"]]),
            "phases": phases,
        })
    receipt = {"schema": "r447-pf6-alignment-withdrawals/1",
               "base": "c85b99cf29fcfb0b955c029a1d380f9666fe0808",
               "withdrawals": rows}
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if all(row["baselineMutantRestoredExit"] == [0, 1, 0]
                    and row["sourceRestoredExactly"] for row in rows) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--phase", choices=["baseline", "mutant", "restored"])
    options = parser.parse_args()
    if bool(options.case) != bool(options.phase):
        parser.error("--case and --phase must be supplied together")
    return execute(options.case, options.phase) if options.case else supervise()


if __name__ == "__main__":
    raise SystemExit(main())
