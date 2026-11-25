#!/usr/bin/env python3
"""Local PF-6 App projection withdrawals; never writes the official ledger.

Each immutable test method runs on baseline, uniquely withdrawn native source,
and restored bytes. Uses the existing bridge assertion/death classifier and
original build/child timeouts. All mutation/build products stay outside repo.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import binaries
import mutation_bridge
import pf6_mutation_check as runner

SOURCE = "geometry-web/panel_fill_builder_bridge.inc"
SUITE = "tests.test_panel_fill_builder_app_view.PanelFillBuilderAppView."
MUTATIONS = [
    {"id": "PF6_APP_DROP_SIXTH_CAPABILITY",
     "source": "geometry-web/panel_fill_bridge.inc",
     "old": '\\"create-from-fill-grid\\",\\"suggest-timbers\\"',
     "new": '\\"create-from-fill-grid\\"',
     "method": "tests.test_panel_fill_ui_contract.PanelFillUiContract.test_read_scoped_delivery_does_not_claim_full_product",
     "assertion": "PF6_UI_WIRE_ACTIONS_EXACT"},
    {"id": "PF6_APP_PROJECT_WRONG_WORLD",
     "old": "if(!json_panel_fill_ui_contract(before,after,proposal->revision,valid,FS_DIAGNOSTIC_INVALID,error))complete=false;",
     "new": "if(!json_panel_fill_ui_contract(before,before,proposal->revision,valid,FS_DIAGNOSTIC_INVALID,error))complete=false;",
     "test": "test_selected_projection_matches_independent_geometry_and_r43_scan",
     "assertion": "PF6_APP_SELECTED_R43_SAME_WORLD"},
    {"id": "PF6_APP_REBIND_EQUAL_HOST_SOURCE",
     "old": "pf6_ui_dimension(after,&host->h,NULL,UINT32_MAX,host->id,TIMBER_ROLE_PRIMARY,1)",
     "new": "pf6_ui_dimension(after,&proposal->input.b,NULL,UINT32_MAX,host->id,TIMBER_ROLE_PRIMARY,1)",
     "test": "test_existing_equal_height_source_and_grid_preference_are_preserved",
     "assertion": "PF6_APP_PRESERVE_HOST_H_NAME"},
    {"id": "PF6_APP_WRONG_FINAL_LENGTH",
     "old": "anchor->placement_id,(long long)center,(long long)timber->length,(long long)anchor->uv.u",
     "new": "anchor->placement_id,(long long)center,(long long)(timber->length+1),(long long)anchor->uv.u",
     "test": "test_selected_projection_matches_independent_geometry_and_r43_scan",
     "assertion": "PF6_APP_FINAL_MEMBER_LENGTH"},
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.out.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("--out must be outside the checkout")
    output.mkdir(parents=True, exist_ok=False)
    if sys.platform != "win32":
        import resource
        hard = resource.getrlimit(resource.RLIMIT_STACK)[1]
        resource.setrlimit(resource.RLIMIT_STACK, (16777216, hard))
    paths = set(binaries._scan_shared())
    paths.update((ROOT / "tests").glob("*.py"))
    paths.update((ROOT / "tests").glob("*.c"))
    paths.update(ROOT.glob("*.scene"))
    paths.update((ROOT / "tests/fixtures").rglob("*.scene"))
    original = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in sorted(paths) if p.is_file()}
    runner.write_json(output / "sources.json", {p: {"bytes": len(raw), "sha256": runner.sha(raw)}
                                             for p, raw in original.items()})
    report = {"schema": "pf6-app-projection-withdrawals/1", "official_ledger": False,
              "source": SOURCE, "source_sha256": runner.sha(original[SOURCE]), "mutations": []}
    with tempfile.TemporaryDirectory(prefix="pf6-app-view-withdraw-") as temporary:
        work = Path(temporary)
        for relative, raw in original.items():
            target = work / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        baseline, baseline_build = runner.build(work, output / "binaries/base", output, "base-build")
        report["baseline_build"] = baseline_build
        for definition in MUTATIONS:
            folder = output / definition["id"]
            methods = [definition["method"]] if "method" in definition else [SUITE + definition["test"]]
            source = definition.get("source", SOURCE)
            before = runner.judge(work, baseline, methods, folder, "baseline")
            if mutation_bridge.classify(before, methods) != "survived":
                raise RuntimeError(definition["id"] + ": baseline failed")
            old, new = definition["old"].encode(), definition["new"].encode()
            raw = original[source]
            if raw.count(old) != 1:
                raise RuntimeError(definition["id"] + ": nonunique source anchor")
            try:
                (work / source).write_bytes(raw.replace(old, new, 1))
                mutant, built = runner.build(work, output / "binaries" / definition["id"], folder, "mutant-build")
                withdrawn = runner.judge(work, mutant, methods, folder, "withdrawn")
            finally:
                (work / source).write_bytes(raw)
            restored = runner.judge(work, baseline, methods, folder, "restored")
            named = bool(withdrawn["result"]) and any(
                definition["assertion"] in failure.get("detail", "")
                for failure in withdrawn["result"].get("failures", []))
            item = {"definition": definition, "baseline": before, "build": built,
                    "withdrawn": withdrawn, "restored": restored, "named_assertion": named,
                    "exits": [before["exit_code"], withdrawn["exit_code"], restored["exit_code"]],
                    "classification": mutation_bridge.classify(withdrawn, methods)}
            report["mutations"].append(item)
            report["original_product_unchanged"] = (ROOT / source).read_bytes() == raw
            runner.write_json(output / "results.json", report)
            print(definition["id"], item["classification"], item["exits"], flush=True)
            if (item["exits"] != [0, 1, 0] or not named or item["classification"] != "killed"
                    or not report["original_product_unchanged"]):
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
