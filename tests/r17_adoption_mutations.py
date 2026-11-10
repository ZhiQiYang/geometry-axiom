#!/usr/bin/env python3
"""Named R17 companion withdrawals in a disposable copy; never edit SSOT bytes.

Run after the prescribed decision record and canonical reader synchronization:
  python3 tests/r17_adoption_mutations.py --out /absolute/new/evidence-directory
Only the model compatibility shim, adoption gate or plain explanation is changed
in TEMP. A freshly built native adapter is reused because no C input is mutated.
Every case runs its named test before, during and after withdrawal. A timeout,
error, skip or unrelated failing method never counts as a killed mutation.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

MODEL = "geometry-core/modeling/__init__.py"
ADOPTION = "tests/test_domain_decoupling_adoption.py"
PLAIN = "geometry-guide/公理層-白話.md"
COMPAT = "test_engineering_model_compatibility.BoundaryPairAdoptionCompatibility."
TEXT = "test_domain_decoupling_adoption.BoundaryPairAdoptionIntegrity."
INPUTS = (MODEL, ADOPTION, PLAIN, "tests/test_engineering_model_compatibility.py",
          "tests/geo261_adoption_mutations.py", "tests/r17_adoption_mutations.py",
          "tests/test_domain_decoupling_proposal.py", "tests/fixtures/r17-approved-delta.json",
          "tests/fixtures/r17-main-343a8abe/profile.json", "tests/fixtures/r17-main-343a8abe/stagger.json",
          "tests/fixtures/r17-main-343a8abe/card.json", "公理層.md", "決策佇列.md")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, message):
    if not ok:
        raise AssertionError(message)


def replace_once(text, before, after):
    need(text.count(before) == 1, "mutation anchor must occur once: " + before[:100])
    return text.replace(before, after, 1)


def drop_guard(text, code):
    nodes = [node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.Expr)
             and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
             and node.value.func.id == "require" and len(node.value.args) > 1
             and isinstance(node.value.args[1], ast.Constant) and node.value.args[1].value == code]
    need(len(nodes) == 1, "require guard must occur once: " + code)
    node = nodes[0]
    lines = text.splitlines(keepends=True)
    lines[node.lineno - 1:node.end_lineno] = [" " * node.col_offset + "pass  # named withdrawal: " + code + "\n"]
    return "".join(lines)


def drop_era(text, suffix):
    rows = [line for line in text.splitlines(keepends=True)
            if line.startswith("        if supplied_version not in ") and line.endswith(suffix + "\n")]
    need(len(rows) == 1, "source-era anchor must occur once: " + suffix)
    return replace_once(text, rows[0], rows[0].replace(" | PRE_BOUNDARY_PAIR_AXIOM_VERSIONS", ""))


def cases():
    reopen = COMPAT + "test_r17_previous_main_packages_reopen_without_losing_any_source_or_geometry"
    eras = COMPAT + "test_r17_previous_main_retains_each_existing_source_era_permission"
    pair = 'PRE_BOUNDARY_PAIR_AXIOM_VERSIONS = frozenset({\n    ("0fd8cacf799ed6ddf0fa7588243aa4e4bbb94c18", "c66c48e50e0caceef42721c79700365f090f5c48d297abba41993eeb40dba9b7"),\n})'
    result = [
        ("R17_M01_DROP_RELEASED_PAIR", MODEL, lambda text: replace_once(text, pair, "PRE_BOUNDARY_PAIR_AXIOM_VERSIONS = frozenset()"), reopen),
        ("R17_M02_DROP_CARD_ERA", MODEL, lambda text: replace_once(text,
            next(line for line in text.splitlines(keepends=True) if line.startswith("CARD_REFERENCE_AXIOM_VERSIONS = ")),
            next(line for line in text.splitlines(keepends=True) if line.startswith("CARD_REFERENCE_AXIOM_VERSIONS = ")).replace(" | PRE_BOUNDARY_PAIR_AXIOM_VERSIONS", "")), reopen),
    ]
    endings = (
        ("PROFILE", " | PRE_BOUNDARY_PAIR_AXIOM_VERSIONS and ("),
        ("SUBDIVISION", ' and "grid-subdivision-rules/1" in scene_required_capabilities(definitions["base_scene"]):'),
        ("STAGGER", ' and _scene_uses_stagger(definitions["base_scene"]):'),
        ("PARAMETER", ' and (PARAMETER_CAPABILITY in scene_required_capabilities(definitions["base_scene"]) or PARAMETER_CAPABILITY in manifest["capabilities"]):'),
        ("INFINITE", ' and _scene_uses_infinite_grid(definitions["base_scene"]):'),
        ("GRID", ' and _scene_uses_grid_system(definitions["base_scene"]):'),
    )
    for number, (name, suffix) in enumerate(endings, 3):
        result.append((f"R17_M{number:02d}_DROP_{name}_ERA", MODEL,
                       lambda text, suffix=suffix: drop_era(text, suffix), eras))
    for number, code, target in (
            (9, "R17_APPROVAL", "test_r17_direction_approval_or_misplaced_full_text_record_cannot_authorize_the_text"),
            (10, "R17_APPROVED_SOURCE", "test_r17_approved_blob_rejects_byte_changes_omission_and_unapproved_new_clauses"),
            (11, "R17_FROZEN_DELTA", "test_r17_delta_cannot_be_rewritten_with_the_current_document")):
        result.append((f"R17_M{number:02d}_DROP_{code}", ADOPTION,
                       lambda text, code=code: drop_guard(text, code), TEXT + target))
    result.extend([
        ("R17_M12_DROP_PLAIN_D16A", PLAIN,
         lambda text: replace_once(text, text[text.index("## D16a\n"):text.index("## D17\n")], ""),
         TEXT + "test_r17_plain_explanation_covers_the_complete_adopted_scope"),
        ("R17_M13_DROP_CURRENT_PAIR", MODEL, lambda text: replace_once(text,
            'AXIOM_REVISION = "347bb01d411c9a656cae213d5cec81409445cf14"\nAXIOM_SHA256 = "13ff6cec70900b55271d9350ca31119f31ad9b20245204d67f49576ca5219712"',
            'AXIOM_REVISION = "0fd8cacf799ed6ddf0fa7588243aa4e4bbb94c18"\nAXIOM_SHA256 = "c66c48e50e0caceef42721c79700365f090f5c48d297abba41993eeb40dba9b7"'),
         COMPAT + "test_r17_adopted_source_pair_and_executor_scope_are_exact"),
        ("R17_M14_DROP_ADOPTION_CHAIN", ADOPTION, lambda text: replace_once(text,
            '        actual = restore_pre_r17_source(actual, (ROOT / "決策佇列.md").read_bytes())\n', ""),
         "test_domain_decoupling_adoption.AdoptionIntegrity.test_actual_ssot_is_the_full_approved_upstream_preserving_adoption"),
    ])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    need(not out.is_relative_to(root), "evidence directory must be outside the repository")
    out.mkdir(parents=True, exist_ok=False)
    original = {name: (root / name).read_bytes() for name in INPUTS}
    report = {"schema": "r17-companion-withdrawals/1", "startedAt": datetime.now(timezone.utc).isoformat(),
              "ours": "73d84f6916b3f09a3bf11ecfbe2761468c277379",
              "main": "343a8abe83029dd883e5e5b1b8e3112411fefe81",
              "mergedBaseTree": "a621fafbf8329c4451908d85fb19cf3f5a388c72",
              "inputSha256": {name: sha(data) for name, data in original.items()}, "cases": []}
    status = 1
    try:
        with tempfile.TemporaryDirectory(prefix="r17-companion-withdrawals-") as directory:
            mirror = Path(directory)
            for folder in ("geometry-core", "geometry-app", "geometry-templates", "geometry-web", "geometry-guide", "tests"):
                shutil.copytree(root / folder, mirror / folder,
                                ignore=shutil.ignore_patterns("__pycache__", ".git", "evidence", "node_modules", "screens"))
            for name in ("current_geometry.c", "公理層.md", "決策佇列.md"):
                shutil.copy2(root / name, mirror / name)
            adapter = mirror / "r17-model-base"
            env = os.environ.copy()
            env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
                       PYTHONPATH=os.pathsep.join((str(mirror / "tests"), str(mirror))))
            env.pop("GEOMETRY_MODEL_BASE", None)
            env.pop("GEOMETRY_PROPOSAL_ROOT", None)
            build = subprocess.run([sys.executable, "-B", "-c",
                "import sys,shutil;sys.path.insert(0,'geometry-core');from modeling.base import _build_adapter;shutil.copy2(_build_adapter(),sys.argv[1])",
                str(adapter)], cwd=mirror, env=env, capture_output=True, timeout=args.timeout)
            (out / "adapter-build.stdout").write_bytes(build.stdout)
            (out / "adapter-build.stderr").write_bytes(build.stderr)
            need(build.returncode == 0 and adapter.is_file(), "native adapter build was blocked or failed")
            env["GEOMETRY_MODEL_BASE"] = str(adapter)
            report["adapterSha256"] = sha(adapter.read_bytes())

            def run(label, target):
                command = [sys.executable, "-B", "-m", "unittest", "-v", target]
                done = subprocess.run(command, cwd=mirror, env=env, capture_output=True, timeout=args.timeout)
                (out / (label + ".stdout")).write_bytes(done.stdout)
                (out / (label + ".stderr")).write_bytes(done.stderr)
                (out / (label + ".exit-code.txt")).write_text(str(done.returncode) + "\n")
                text = done.stderr.decode("utf-8", "replace")
                need(re.search(r"Ran 1 test in ", text) is not None, label + ": named test did not run exactly once")
                need("ERROR:" not in text and "skipped" not in text, label + ": errors/skips are not assertion witnesses")
                need((mirror / "公理層.md").read_bytes() == original["公理層.md"], "SSOT bytes changed")
                return {"command": command, "exit": done.returncode, "stdoutSha256": sha(done.stdout),
                        "stderrSha256": sha(done.stderr)}, text

            for name, path, withdraw, target in cases():
                product = mirror / path
                positive = product.read_bytes()
                before, _ = run(name + "-before", target)
                need(before["exit"] == 0, name + ": baseline must be green")
                mutant = withdraw(positive.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
                need(mutant != positive, name + ": withdrawal did not change its target")
                try:
                    product.write_bytes(mutant)
                    red, stderr = run(name + "-mutant", target)
                    method = target.rsplit(".", 1)[1]
                    need(red["exit"] == 1 and "FAILED (failures=" in stderr and "FAIL: " + method in stderr,
                         name + ": only the named assertion failure counts as killed")
                finally:
                    product.write_bytes(positive)
                after, _ = run(name + "-restored", target)
                need(after["exit"] == 0 and product.read_bytes() == positive, name + ": restoration did not return green")
                report["cases"].append({"id": name, "path": path, "test": target, "verdict": "killed",
                    "positiveSha256": sha(positive), "mutantSha256": sha(mutant), "before": before, "mutant": red, "restored": after})
                print(name + ": 0 -> 1 -> 0", flush=True)
        need(len(report["cases"]) == 14, "all fourteen named withdrawals must finish")
        report["verdict"] = "passed"
        status = 0
    except subprocess.TimeoutExpired as error:
        report.update(verdict="blocked", error="timeout: " + str(error))
        status = 2
    except Exception as error:
        report.update(verdict="failed", error=str(error))
    finally:
        unchanged = all((root / name).read_bytes() == data for name, data in original.items())
        report["originalInputsUnchanged"] = unchanged
        if not unchanged:
            report["verdict"], status = "failed", 1
        report["finishedAt"] = datetime.now(timezone.utc).isoformat()
        (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"], "killed": len(report["cases"]), "originalInputsUnchanged": unchanged}, ensure_ascii=False))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
