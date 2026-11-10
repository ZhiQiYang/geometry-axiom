"""Execute the 16 native R14 fault contracts from issue #57, comment 6677738068.

Each fault runs in its own copied source tree. The working repository is read
only. Every item requires its own green baseline, one exact source edit, an
assertion failure in its named judge, byte-for-byte source restoration, a fresh
binary check, and the same judge green again. Compiler errors, crashes, skips,
timeouts and mismatched source anchors are blocked, never killed. Results are
written only to --output; this runner never edits tests/mutants_results.json.

Example (the -O0 option is a recorded fault-isolation build, not the -O2 release
verification; baseline, fault and restoration use the identical chosen flags):

  python tests/mutation_r14_repeat_panel.py --output /tmp/r14-mutations --optimization O0

Use --id repeatedly to divide the independent faults between isolated workers.
The complete native suite must be green before any selected fault is attempted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "tests"
sys.path.insert(0, str(HERE))
import binaries
from mutation_bridge import classify

BASE = "83d4ca22e3129d64bbb3b8dd024e950250992eee"
# Re-pinned when this slice moved onto main 6fd9e8b1: the approved R17 text
# (blob 9d713b77) plus the approved R14 P patch gives blob b3472f2d (#374).
AXIOM_BLOB = "b3472f2d2b481f7c889945a092fb9b3e911dc027"
PREFIX = "tests.test_r14_repeat_panel.R14RepeatPanelNative."
METHODS = [
    "test_01_literal_mixed_dual_panel_phase_anchor_and_inner_lines",
    "test_02_binding_and_placed_refs_keep_large_signed_cells",
    "test_03_unconfigured_upstream_edit_preserves_rule_or_rejects_whole_candidate",
    "test_04_nonintegral_full_pitch_never_rounds_or_allocates_remainder",
    "test_05_missing_finite_and_d10b_sources_remain_rejected",
    "test_06_same_pitch_source_kind_switch_keeps_rules_highwater_and_identity",
    "test_07_v2_scene_roundtrip_missing_or_downgraded_marker_is_atomic",
    "test_08_replay_encountered_panel_rule_requires_v2_after_source_delete",
    "test_09_panel_without_rule_or_with_only_highwater_does_not_require_v2",
    "test_10_cancel_create_delete_and_recreate_preserve_allocator",
    "test_11_repeat_only_original_geometry_and_minimum_capability_stay_unchanged",
    "test_12_parameter_and_card_sources_resolve_before_exactness_and_are_not_flattened",
    "test_13_native_slice_capability_is_explicit_without_claiming_complete_host_support",
]


def fault(identifier, path, before, after, method, marker):
    return {"id": identifier, "path": path, "before": before, "after": after,
            "tests": [PREFIX + METHODS[method - 1]], "marker": marker}


MUTANTS = [
    fault("R14_NATIVE_K_PANEL_GATE_RESTORED", "geometry-core/kernel/grid_store.c",
          "if (!geo_grid_axis_is_infinite(&system->axis[axis]) || system->axis[axis].stagger_set) {",
          "if (system->axis[axis].source != GEO_GRID_SOURCE_REPEAT || system->axis[axis].stagger_set) {",
          1, "SOURCE_KIND"),
    fault("R14_NATIVE_W_PANEL_GATE_RESTORED", "geometry-templates/woodworking/native/grid_rules.c",
          "if(!target->source || !geo_grid_axis_is_infinite(&target->source->axis[0]) ||\n"
          "        !geo_grid_axis_is_infinite(&target->source->axis[1]) || target->source->axis[0].stagger_set ||",
          "if(!target->source || target->source->axis[0].source!=GEO_GRID_SOURCE_REPEAT ||\n"
          "        target->source->axis[1].source!=GEO_GRID_SOURCE_REPEAT || target->source->axis[0].stagger_set ||",
          1, "R14_NATIVE_QUERY"),
    fault("R14_NATIVE_PANEL_BODY_AS_PITCH", "geometry-core/kernel/grid_store.c",
          "{ return axis->source == GEO_GRID_SOURCE_REPEAT ? axis->step : geo_period_pitch(axis->body, axis->gap); }",
          "{ return axis->source == GEO_GRID_SOURCE_REPEAT ? axis->step : axis->body; }",
          1, "DIVISION_NOT_EXACT"),
    fault("R14_NATIVE_ODD_GAP_ROUND_UP", "geometry-core/kernel/grid.c",
          "{ return geo_period_body(anchor,body,gap,k)+body+gap/2; }",
          "{ return geo_period_body(anchor,body,gap,k)+body+(gap+1)/2; }",
          1, "odd-gap-floor"),
    fault("R14_NATIVE_SKIP_DIVISIBILITY", "geometry-core/kernel/grid_store.c",
          "for (int axis = 0; axis < 2; ++axis) if (geo_grid_axis_pitch(&system->axis[axis]) % rule->divisions[axis]) {",
          "for (int axis = 0; axis < 2; ++axis) if (system->axis[axis].source != GEO_GRID_SOURCE_REPEAT_BODY_GAP && geo_grid_axis_pitch(&system->axis[axis]) % rule->divisions[axis]) {",
          4, "R14_REJECTION_REQUIRED"),
    fault("R14_NATIVE_STAGGER_SCOPE_OPENED", "geometry-core/kernel/grid_store.c",
          "if (!geo_grid_axis_is_infinite(&system->axis[axis]) || system->axis[axis].stagger_set) {",
          "if (!geo_grid_axis_is_infinite(&system->axis[axis])) {",
          5, "R14_REJECTION_REQUIRED"),
    fault("R14_NATIVE_SOURCE_EDIT_DROPS_RULES", "geometry-core/kernel/grid_store.c",
          "        memcpy(next.rules, old->rules, sizeof next.rules);\n    }\n    if (!geo_grid_systems_put(store, &next))",
          "        memcpy(next.rules, old->rules, sizeof next.rules);\n"
          "        if ((next.axis[0].source != old->axis[0].source && next.axis[0].source == GEO_GRID_SOURCE_REPEAT_BODY_GAP) ||\n"
          "            (next.axis[1].source != old->axis[1].source && next.axis[1].source == GEO_GRID_SOURCE_REPEAT_BODY_GAP)) {\n"
          "            next.rule_count = 0; memset(next.rules, 0, sizeof next.rules);\n"
          "        }\n    }\n    if (!geo_grid_systems_put(store, &next))",
          6, "R14_SOURCE_EDIT_PRESERVES_RULES"),
    fault("R14_NATIVE_UPSTREAM_IGNORES_UNCONFIGURED_RULE", "geometry-templates/woodworking/native/grid_application.c",
          "    return wood_grid_rules_valid(system,error,cap);",
          "    bool valid=wood_grid_rules_valid(system,error,cap);\n"
          "    if(!valid && geo_grid_bindings_count(c->sources)==0 && c->state->count==0 &&\n"
          "        error && strstr(error,\"DIVISION_NOT_EXACT\"))return true;\n"
          "    return valid;",
          3, "R14_REJECTION_REQUIRED"),
    fault("R14_NATIVE_ACCEPT_STRIPPED_V2", "geometry-core/grid_subdivision.inc",
          "if((g_rule_scene_panel_encountered || grid_subdivision_panel_used(w)) && !g_rule_scene_panel_required)",
          "if(false && (g_rule_scene_panel_encountered || grid_subdivision_panel_used(w)) && !g_rule_scene_panel_required)",
          7, "R14_CAPABILITY_STRIP_OR_DOWNGRADE"),
    fault("R14_NATIVE_FORGET_ENCOUNTERED_ON_DELETE", "geometry-core/grid_subdivision.inc",
          "if((g_rule_scene_panel_encountered || grid_subdivision_panel_used(w)) && !g_rule_scene_panel_required)",
          "if(grid_subdivision_panel_used(w) && !g_rule_scene_panel_required)",
          8, "R14_ENCOUNTERED_CAPABILITY_NOT_FINAL_STATE_ONLY"),
    fault("R14_NATIVE_HIGHWATER_FORCES_V2", "geometry-core/grid_subdivision.inc",
          "if(s->rule_count && (s->axis[0].source==GRID_SRC_REPEAT_PANEL || s->axis[1].source==GRID_SRC_REPEAT_PANEL))return true;",
          "if((s->rule_count || s->next_rule_key!=1) && (s->axis[0].source==GRID_SRC_REPEAT_PANEL || s->axis[1].source==GRID_SRC_REPEAT_PANEL))return true;",
          9, "panel-highwater-only-v1"),
    fault("R14_NATIVE_SIGNED_CELL_DOUBLE", "geometry-web/grid_subdivision_bridge.inc",
          "(long long)cell->cell[0],(long long)cell->cell[1],(long long)cell->bounds.min_u,",
          "(long long)(double)cell->cell[0],(long long)(double)cell->cell[1],(long long)cell->bounds.min_u,",
          2, "9007199254740993"),
    fault("R14_NATIVE_UNPLACED_REF_FABRICATED", "geometry-web/grid_subdivision_bridge.inc",
          "if (query->has_placed_ref)", "if (true)", 1, "R14_UNPLACED_REF_NULL"),
    fault("R14_NATIVE_CANCEL_CONSUMES_KEY", "geometry-web/web_bridge.c",
          '    bool ok=feed_line("input",++g_input_line_no,text,&g_world);',
          '    bool ok=feed_line("input",++g_input_line_no,text,&g_world);\n'
          '    if(g_preview.ready && g_preview.token!=token && g_preview.valid &&\n'
          '        !strncmp(text,"grid-source-rule ",17) && strstr(text," create ")) {\n'
          '        for(size_t i=0;i<geo_grid_systems_count(&g_world.geo.grid_store);++i) {\n'
          '            const GridSystem *live=geo_grid_systems_at(&g_world.geo.grid_store,i);\n'
          '            const GridSystem *next=world_find_grid_system(&g_preview.transaction->after,live->id);\n'
          '            if(next && next->next_rule_key!=live->next_rule_key) {\n'
          '                GridSystem allocated=*live;allocated.next_rule_key=next->next_rule_key;\n'
          '                app_grid_system_put(&g_world,&allocated,app_grid_system_main_along(&g_world,live->id));\n'
          '            }\n'
          '        }\n'
          '    }',
          10, "R14_RULE_PREVIEW_READONLY"),
    fault("R14_NATIVE_CARD_FLATTENED_TO_EFFECTIVE", "geometry-core/grid_systems.inc",
          'if(a->card_length)fputs("card",out);else grid_parameter_dump(out,a->body,a->parameters[2]);',
          'if(a->card_length)fputs("card",out);else fprintf(out,"%lld",(long long)a->body);',
          12, "R14_SOURCE_DEFINITION_NOT_EFFECTIVE_VALUE"),
    fault("R14_NATIVE_EQUAL_VALUE_REBIND_SKIPPED", "geometry-core/card_reference.inc",
          '        s->card_reference=ref;if(!grid_card_mark(s))return false;',
          '        GridSystem resolved=*s;resolved.card_reference=ref;char comparison_error[512]="";\n'
          '        if(s->card_reference.set && grid_card_mark(&resolved) && grid_card_resolve(w,&resolved,comparison_error,sizeof comparison_error) &&\n'
          '            resolved.axis[0].step==s->axis[0].step && resolved.axis[0].body==s->axis[0].body &&\n'
          '            resolved.axis[1].step==s->axis[1].step && resolved.axis[1].body==s->axis[1].body)return true;\n'
          '        s->card_reference=ref;if(!grid_card_mark(s))return false;',
          12, "R14_EQUAL_VALUE_DIFFERENT_SOURCE"),
]

COPY_TESTS = ("__init__.py", "_bridge.py", "binaries.py", "bridge_mutation_oracle.py",
              "mutation_bridge.py", "test_r14_repeat_panel.py", "mutation_r14_repeat_panel.py")
FIXTURE = "tests/fixtures/r14_repeat_panel_candidate.json"
BUILD_CODE = r'''
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "tests"))
import binaries
binaries.OUT_DIR = Path(sys.argv[2])
b = binaries.BY_NAME["bridge"]
if sys.argv[3] == "O0":
    b.posix_flags = ["-O0" if f == "-O2" else f for f in b.posix_flags]
    b.win_flags = ["/Od" if f == "/O2" else f for f in b.win_flags]
result = binaries.build_one(b)
info = binaries.inspect_one(b)
print("R14_BUILD_RESULT " + json.dumps({"build": result.__dict__, "info": info.as_dict()}))
raise SystemExit(0 if result.ok and info.state == "fresh" else 2)
'''
ORACLE_CODE = r'''
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "tests"))
import binaries
if sys.argv[2] == "O0":
    b = binaries.BY_NAME["bridge"]
    b.posix_flags = ["-O0" if f == "-O2" else f for f in b.posix_flags]
    b.win_flags = ["/Od" if f == "/O2" else f for f in b.win_flags]
import bridge_mutation_oracle
raise SystemExit(bridge_mutation_oracle.main(sys.argv[3:]))
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def environment(output):
    env = os.environ.copy()
    temporary = output / "tmp"
    temporary.mkdir(exist_ok=True)
    env.update(PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(temporary), TEMP=str(temporary), TMP=str(temporary))
    return env


def run(command, cwd, log, env, timeout):
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=timeout)
        stdout, stderr, code, timed_out = result.stdout, result.stderr, result.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout or ""
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr or ""
        code, timed_out = 2, True
    log.with_suffix(".stdout.txt").write_text(stdout, encoding="utf-8", newline="\n")
    log.with_suffix(".stderr.txt").write_text(stderr, encoding="utf-8", newline="\n")
    row = {"command": command, "cwd": str(cwd), "exit_code": code, "timed_out": timed_out,
           "seconds": round(time.monotonic() - started, 3), "stdout_sha256": sha(stdout.encode()),
           "stderr_sha256": sha(stderr.encode())}
    for line in stdout.splitlines():
        if line.startswith("GEOMETRY_BRIDGE_MUTATION_RESULT "):
            row["result"] = json.loads(line.split(" ", 1)[1])
        if line.startswith("R14_BUILD_RESULT "):
            row["build_result"] = json.loads(line.split(" ", 1)[1])
    return row


def build(source, out, optimization, log, env):
    row = run([sys.executable, "-c", BUILD_CODE, str(source), str(out), optimization],
              source, log, env, 300)
    binary = out / binaries.BY_NAME["bridge"].exe
    sidecar = binary.with_name(binary.name + binaries.SIDECAR_SUFFIX)
    if row["exit_code"] == 0 and sidecar.is_file():
        row["sidecar"] = json.loads(sidecar.read_text(encoding="utf-8"))
        row["binary_sha256"] = sha(binary.read_bytes())
    return binary, row


def oracle(source, binary, methods, optimization, log, env):
    return run([sys.executable, "-c", ORACLE_CODE, str(source), optimization, str(binary), *methods],
               source, log, env, 180)


def source_files():
    paths = {p.relative_to(ROOT).as_posix() for p in binaries._scan_shared() if p.is_file()}
    paths.update("tests/" + name for name in COPY_TESTS)
    paths.add(FIXTURE)
    paths.add("公理層.md")
    return sorted(paths)


def copy_source(destination, paths):
    for relative in paths:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def raw_hashes(directory, paths):
    return {path: sha((directory / path).read_bytes()) for path in paths}


def inject(source, item):
    path = source / item["path"]
    raw = path.read_bytes()
    text = raw.replace(b"\r\n", b"\n").decode("utf-8")
    count = text.count(item["before"])
    if count != 1:
        raise ValueError("one exact mutation anchor required; found %d for %s" % (count, item["id"]))
    changed = text.replace(item["before"], item["after"], 1).encode("utf-8")
    if b"\r\n" in raw and raw.count(b"\r\n") == raw.count(b"\n"):
        changed = changed.replace(b"\n", b"\r\n")
    if changed == raw:
        raise ValueError("mutation did not change source bytes")
    path.write_bytes(changed)
    return raw


def main(argv=None):
    if sys.flags.optimize:
        raise RuntimeError("optimized Python cannot serve as an assertion oracle")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--optimization", choices=("O0", "O2"), default="O2")
    parser.add_argument("--id", action="append", dest="ids", choices=[m["id"] for m in MUTANTS])
    args = parser.parse_args(argv)
    # A label is not a source pin. Verify the approved clauses and actual git
    # ancestry before copying or building anything; record both for each item.
    axiom = (ROOT / "公理層.md").read_bytes().replace(b"\r\n", b"\n")
    axiom_blob = hashlib.sha1(b"blob " + str(len(axiom)).encode() + b"\0" + axiom).hexdigest()
    if axiom_blob != AXIOM_BLOB:
        parser.error("approved R14 axiom blob mismatch: " + axiom_blob)
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    ancestry = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASE, head],
                              capture_output=True, text=True)
    if ancestry.returncode != 0:
        parser.error("the declared base must be an ancestor of the actual HEAD: " + head)
    source_guard = {"specification_base": BASE, "actual_head": head,
                    "actual_axiom_blob": axiom_blob, "axiom_bytes_lf": len(axiom),
                    "axiom_sha256_lf": sha(axiom), "base_is_ancestor": True}
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("--output must be outside the working repository")
    if output.exists() and any(output.iterdir()):
        parser.error("--output must be empty so an earlier receipt cannot be overwritten")
    output.mkdir(parents=True, exist_ok=True)
    env = environment(output)
    selected = [m for m in MUTANTS if not args.ids or m["id"] in args.ids]
    paths = source_files()
    source_identity = raw_hashes(ROOT, paths)
    baseline = output / "baseline-source"
    copy_source(baseline, paths)
    report = {"schema": "r14-native-mutation-evidence/1", "base": BASE, "axiom_blob": AXIOM_BLOB,
              "source_guard": source_guard,
              "specification": "https://github.com/ZhiQiYang/geometry-axiom/issues/57#issuecomment-6677738068",
              "started_at": datetime.now(timezone.utc).isoformat(), "optimization": args.optimization,
              "source_files_sha256": source_identity, "selected": [m["id"] for m in selected], "items": []}
    binary, report["baseline_build"] = build(baseline, output / "baseline-bin", args.optimization,
                                             output / "baseline-build", env)
    if report["baseline_build"]["exit_code"] != 0:
        report["status"] = "blocked: baseline compilation/freshness"
        write_json(output / "evidence.json", report)
        return 2
    all_methods = [PREFIX + name for name in METHODS]
    report["baseline_suite"] = oracle(baseline, binary, all_methods, args.optimization,
                                       output / "baseline-suite", env)
    if classify(report["baseline_suite"], all_methods) != "survived":
        report["status"] = "blocked: native baseline is not fully green"
        write_json(output / "evidence.json", report)
        return 2
    for item in selected:
        folder = output / item["id"]
        folder.mkdir()
        source = folder / "source"
        shutil.copytree(baseline, source)
        record = {"id": item["id"], "path": item["path"], "tests": item["tests"],
                  "source_guard": source_guard,
                  "required_failure_marker": item["marker"], "status": "blocked"}
        record["baseline"] = oracle(source, binary, item["tests"], args.optimization, folder / "baseline", env)
        original = None
        try:
            if classify(record["baseline"], item["tests"]) != "survived":
                raise ValueError("named baseline did not pass")
            original = inject(source, item)
            changed = raw_hashes(source, paths)
            changed_paths = [path for path in paths if changed[path] != source_identity[path]]
            if changed_paths != [item["path"]]:
                raise ValueError("mutation changed an unexpected path set: " + repr(changed_paths))
            record["source_before_sha256"] = source_identity[item["path"]]
            record["source_fault_sha256"] = changed[item["path"]]
            mutant_binary, record["fault_build"] = build(source, folder / "bin", args.optimization,
                                                        folder / "build", env)
            if record["fault_build"]["exit_code"] != 0:
                raise ValueError("fault compilation/freshness failed")
            record["fault"] = oracle(source, mutant_binary, item["tests"], args.optimization,
                                      folder / "fault", env)
        except (OSError, ValueError, RuntimeError) as exc:
            record["blocked_reason"] = str(exc)
        finally:
            if original is not None:
                (source / item["path"]).write_bytes(original)
        record["source_restored_exact"] = raw_hashes(source, paths) == source_identity
        record["restored"] = oracle(source, binary, item["tests"], args.optimization, folder / "restored", env)
        record["restored_binary_reused_after_freshness_check"] = str(binary)
        if record["source_restored_exact"] and classify(record["baseline"], item["tests"]) == "survived" and classify(record["restored"], item["tests"]) == "survived" and "fault" in record:
            verdict = classify(record["fault"], item["tests"])
            detail = "\n".join(f.get("test", "") + "\n" + f.get("detail", "")
                               for f in record["fault"].get("result", {}).get("failures", []))
            if verdict == "killed" and item["marker"] in detail:
                record["status"] = "killed"
            elif verdict == "survived":
                record["status"] = "survived"
            else:
                record.setdefault("blocked_reason", "fault did not hit the named assertion without errors/crashes/skips")
        write_json(folder / "evidence.json", record)
        report["items"].append(record)
        write_json(output / "evidence.json", report)
        print(item["id"] + ": " + record["status"], flush=True)
        # The source bytes and all three structured runs are retained in evidence;
        # temporary copies are disposable and must not consume full-repo space.
        shutil.rmtree(source)
    report["working_source_unchanged"] = raw_hashes(ROOT, paths) == source_identity
    report["counts"] = {name: sum(row["status"] == name for row in report["items"])
                        for name in ("killed", "survived", "blocked")}
    report["status"] = "pass" if report["working_source_unchanged"] and report["counts"]["killed"] == len(selected) else "fail"
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "evidence.json", report)
    print(json.dumps({"status": report["status"], "counts": report["counts"], "evidence": str(output / "evidence.json")}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
