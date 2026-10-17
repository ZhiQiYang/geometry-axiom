"""Bridge-backed mutation records for guards outside the core scene oracle.

Mutants run in a separate, sparse committed checkout. The invoking repository and
its live runtime are never temporarily mutated. Every record includes baseline,
real failing unittest results, restored results, binaries and official sidecars.
"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

PREFIX = "tests.test_parameters_core.ParametersCore."
RESTORED = [
    "tests.test_grid_system_contract.GridSystemContract.test_k2a_parameter_confirmation_receipt_includes_intermediate_deletion",
    *[PREFIX + name for name in [
        "test_delete_then_import_or_redeclare_keeps_the_deletion_receipt",
        "test_referenced_card_rebuild_without_referrer_declaration_rejects",
        "test_referenced_field_omission_and_rebuild_requires_declaration",
        "test_referrer_must_be_declared_after_the_last_card_deletion",
        "test_deletion_tracking_does_not_retire_retained_or_future_fields",
        "test_engineering_base_and_override_declarations_are_independent",
        "test_explicit_unbind_reads_the_present_generation_after_rebuild",
        "test_delete_rebuild_then_unbind_reads_current_99_instead_of_deleted_cache",
        "test_deleted_value_capture_does_not_follow_an_unacknowledged_rebuild",
    ]],
    "tests.test_assembly_parameter_refs.AssemblyParameterRefs.test_missing_zero_reference_rejected_without_world_mutation",
    "tests.test_parameters_deleted_unbind.DeletedSourceUnbind.test_delete_then_unbind_has_identical_dump_to_legal_order",
    "tests.test_section_profile_native.SectionProfileNative.test_delete_parameter_names_section_profile_member_and_run_referrers",
    *[PREFIX + name for name in [
        "test_native_consumers_require_explicit_rebinding_after_parameter_rebuild",
        "test_direct_grid_axis_redeclaration_is_local",
        "test_preview_discloses_only_last_deletion_redeclarations",
        "test_panel_fill_gap_rebuild_requires_prior_reference_change",
        "test_panel_fill_stagger_rebuild_requires_prior_reference_change",
        "test_panel_fill_threshold_rebuild_requires_prior_reference_change",
        "test_separate_transaction_guidance_names_native_owner_after_other_referrers",
    ]],
    # GEO-262 / P-142 B2: whole-card owners in the shared I38 rejection.
    *["tests.test_grid_card_reference.GridCardReference." + name for name in [
        "test_P142_B2_CARD_AND_PANEL_FILL_GAP_SHARE_I38_REJECTION",
        "test_P142_B2_CARD_AND_PANEL_FILL_STAGGER_SHARE_I38_REJECTION",
        "test_P142_B2_CARD_AND_PANEL_FILL_THRESHOLD_SHARE_I38_REJECTION",
    ]],
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def oracle_hash(m, root):
    """Conservative judge closure: all flat Python tests and root scene fixtures.

    This intentionally invalidates these bridge records when any shared Python
    harness changes. The result ledger itself is excluded to avoid self-hashing.
    """
    root = Path(root)
    files = sorted([*root.glob("tests/*.py"), *root.glob("*.scene")])
    rows = [(p.relative_to(root).as_posix(), sha(p.read_bytes().replace(b"\r\n", b"\n"))) for p in files]
    return sha(json.dumps([m["tests"], RESTORED, rows], ensure_ascii=False, separators=(",", ":")).encode())


def classify(receipt, methods):
    """Only completed explicit unittest assertions can kill a mutant."""
    if (not methods or len(set(methods)) != len(methods)
            or type(receipt.get("exit_code")) is not int):
        return "blocked"
    row = receipt.get("result")
    if not isinstance(row, dict) or row.get("schema") != "geometry-bridge-mutation-tests/1":
        return "blocked"
    if (row.get("requested") != methods or row.get("started") != methods
            or type(row.get("total")) is not int or row["total"] != len(methods)):
        return "blocked"
    for name in ("errors", "skipped", "failures"):
        if not isinstance(row.get(name), list):
            return "blocked"
    if (row["errors"] or row["skipped"] or any(type(row.get(k)) is not int or row[k] != 0
                                             for k in ("expected_failures", "unexpected_successes"))):
        return "blocked"
    if row["failures"]:
        for failure in row["failures"]:
            if (not isinstance(failure, dict) or not isinstance(failure.get("test"), str)
                    or not isinstance(failure.get("detail"), str) or not failure["detail"]
                    or not any(failure["test"] == name or failure["test"].startswith(name + " (") for name in methods)):
                return "blocked"
        return "killed" if receipt.get("exit_code") == 1 else "blocked"
    return "survived" if receipt.get("exit_code") == 0 else "blocked"


def _portable(value, root, work, cache):
    for path, marker in [(work, "<work>"), (root, "<repo>"), (cache, "<cache>")]:
        value = value.replace(str(path), marker)
    return value


def _run(argv, cwd, env, folder, label, root, work, cache, timeout=900):
    folder.mkdir(parents=True, exist_ok=True)
    out, err = folder / (label + ".stdout"), folder / (label + ".stderr")
    p, timed_out = None, False
    def terminate_owned():
        if p is None:
            return
        if os.name == "posix":
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        elif p.poll() is None:
            subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                p.kill()
            p.wait(timeout=5)
    try:
        p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=os.name == "posix")
        try:
            stdout, stderr = p.communicate(timeout=timeout); code = p.returncode
        except subprocess.TimeoutExpired:
            timed_out = True; terminate_owned(); stdout, stderr = p.communicate(); code = 124
    except OSError as exc:
        stdout, stderr, code = b"", str(exc).encode(), 127
    except BaseException:
        terminate_owned(); raise
    out.write_bytes(stdout); err.write_bytes(stderr)
    records = [line.removeprefix("GEOMETRY_BRIDGE_MUTATION_RESULT ")
               for line in stdout.decode("utf-8", errors="replace").splitlines()
               if line.startswith("GEOMETRY_BRIDGE_MUTATION_RESULT ")]
    result = None
    if len(records) == 1:
        try:
            result = json.loads(_portable(records[0], root, work, cache))
        except ValueError:
            pass
    return {"command": [_portable(str(a), root, work, cache) for a in argv],
            "exit_code": code, "process_returncode": p.returncode if p else None, "timed_out": timed_out,
            "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
            "stdout_file": label + ".stdout", "stderr_file": label + ".stderr", "result": result}


def _registry(work, out):
    name = "bridge_mutation_registry"
    spec = importlib.util.spec_from_file_location(name, work / "tests/binaries.py")
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    module.OUT_DIR = out
    return module


def _identity(work, out):
    registry = _registry(work, out)
    info = registry.inspect_one(registry.BY_NAME["bridge"])
    if info.state != "fresh":
        raise RuntimeError(info.reason)
    binary = registry.BY_NAME["bridge"].path
    raw = binary.read_bytes()
    side_raw = binary.with_name(binary.name + ".fingerprint.json").read_bytes()
    side = json.loads(side_raw)
    if sha(raw) != side["exe_sha256"]:
        raise RuntimeError("bridge changed after freshness check")
    return {"exe_sha256": sha(raw), "sidecar_sha256": sha(side_raw), "sidecar": side,
            "freshness": info.state}


def _build(work, out, env, folder, label, root, cache):
    script = ('import pathlib,sys;sys.path.insert(0,"tests");import binaries;'
              'binaries.OUT_DIR=pathlib.Path(sys.argv[1]);raise SystemExit(binaries.main(["build","bridge"]))')
    result = _run([sys.executable, "-B", "-c", script, str(out)], work, env, folder, label, root, work, cache)
    if result["exit_code"] != 0:
        raise RuntimeError("official bridge build failed: " + json.dumps(result))
    return result, _identity(work, out)


def _test(work, binary, methods, env, folder, label, root, cache):
    return _run([sys.executable, "-B", "tests/bridge_mutation_oracle.py", str(binary), *methods],
                work, env, folder, label, root, work, cache)


def _metadata_sources(side, m, root, mutated):
    if not isinstance(side.get("files"), dict) or m["file"] not in side["files"]:
        raise ValueError("bridge sidecar does not cover the mutation target")
    for rel, digest in side.get("files", {}).items():
        path = Path(root) / rel
        if not path.resolve().is_relative_to(Path(root).resolve()) or "#" in rel:
            raise ValueError("unexpected bridge source path")
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        if mutated and rel == m["file"]:
            old, new = m["old"].encode(), m["new"].encode()
            if raw.count(old) != 1:
                raise ValueError("mutant anchor not unique")
            raw = raw.replace(old, new, 1)
        if digest != sha(raw):
            raise ValueError("bridge sidecar source mismatch: " + rel)


def execution_problems(mt, m, rec, verdict, src):
    e = rec.get("execution")
    try:
        if not isinstance(e, dict) or e.get("schema") != "geometry-bridge-mutation-execution/1":
            raise ValueError("missing bridge execution receipt")
        if not re.fullmatch(r"[0-9a-f]{40}", e["head"]) or e["tool_sha256"] != mt.tool_hash():
            raise ValueError("bridge execution tool/head")
        if e["methods"] != m["tests"] or e["restored_methods"] != RESTORED:
            raise ValueError("bridge oracle methods changed")
        if classify(e["baseline"], RESTORED) != "survived" or classify(e["restored"], RESTORED) != "survived":
            raise ValueError("bridge baseline/restoration did not pass every declared method")
        if classify(e["mutant"], m["tests"]) != verdict or verdict not in ("killed", "survived"):
            raise ValueError("bridge verdict contradicts actual unittest results")
        killers = [x["test"] for x in e["mutant"]["result"]["failures"]][:mt.KILLED_BY_MAX]
        if verdict == "killed" and rec.get("killed_by") != killers:
            raise ValueError("bridge killed_by contradicts raw assertion results")
        for build in (e["baseline_build"], e["mutant_build"], e["restored_build"]):
            if build["exit_code"] != 0:
                raise ValueError("bridge build did not succeed")
        for label, mutated in (("baseline_identity", False), ("mutant_identity", True), ("restored_identity", False)):
            identity = e[label]
            if identity["freshness"] != "fresh" or identity["exe_sha256"] != identity["sidecar"]["exe_sha256"]:
                raise ValueError("bridge binary/sidecar mismatch")
            _metadata_sources(identity["sidecar"], m, src.root, mutated)
        if e["platform"] == "posix" and e["baseline_identity"]["exe_sha256"] != e["restored_identity"]["exe_sha256"]:
            raise ValueError("restored bridge bytes differ from baseline")
        for row in (e["baseline"], e["mutant"], e["restored"], e["baseline_build"], e["mutant_build"], e["restored_build"]):
            for key in ("stdout_sha256", "stderr_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", row[key]):
                    raise ValueError("missing bridge raw output hash")
        for row, methods in [(e["baseline"], RESTORED), (e["mutant"], m["tests"]), (e["restored"], RESTORED)]:
            if row["command"][2] != "tests/bridge_mutation_oracle.py" or row["command"][-len(methods):] != methods:
                raise ValueError("bridge oracle command differs from declared methods")
        if not e.get("byte_restored") or e["oracle_sha256"] != oracle_hash(m, src.root):
            raise ValueError("bridge source/oracle restoration")
        if e["platform"] == os.name:
            artifact = mt.MUT_ROOT / m["id"] / "bridge-mutant" / ("bridge.exe" if os.name == "nt" else "bridge")
            if artifact.exists() and sha(artifact.read_bytes()) != e["mutant_identity"]["exe_sha256"]:
                raise ValueError("bridge executable artifact changed")
    except (KeyError, TypeError, ValueError, OSError) as exc:
        return [str(exc)]
    return []


def run_pass(mt, mutants, root, results_path, today=None):
    root, cache = Path(root).resolve(), mt.MUT_ROOT.resolve()
    src = mt.Sources(root); today = today or datetime.date.today().isoformat()
    records = mt.load_records(results_path)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=root).decode().splitlines()
    if any(p != "tests/mutants_results.json" for p in changed):
        raise RuntimeError("bridge mutations require a committed source; only the output ledger may be dirty")
    work = cache / "_bridge-work" / head / "repo"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GEOMETRY_", "MUTATE_", "GIT_"))}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    env.pop("PYTHONOPTIMIZE", None)
    if not work.exists():
        work.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--shared", "--no-checkout", str(root), str(work)], check=True, env=env)
        subprocess.run(["git", "sparse-checkout", "set", "--no-cone", "/*", "!/tests/evidence/", "!/tests/release-evidence/"], cwd=work, check=True, env=env)
        subprocess.run(["git", "-c", "core.autocrlf=false", "checkout", "--detach", head], cwd=work, check=True, env=env)
    if (subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=work).decode().strip() != head
            or mt.Sources(work).closure != src.closure or subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=work).strip()):
        raise RuntimeError("bridge scratch checkout is not the exact committed source")
    base_dir = cache / "_bridge-baseline" / head
    baseline_build, baseline_identity = _build(work, base_dir, env, base_dir, "baseline-build", root, cache)
    binary_name = "bridge.exe" if os.name == "nt" else "bridge"
    baseline = _test(work, base_dir / binary_name, RESTORED, env, base_dir, "baseline", root, cache)
    if classify(baseline, RESTORED) != "survived":
        raise RuntimeError("bridge baseline blocked: all %d methods must actually pass" % len(RESTORED))
    for m in mutants:
        judge = oracle_hash(m, root); folder = cache / m["id"]; folder.mkdir(parents=True, exist_ok=True)
        kind, why = mt.definition_kind(m, src)
        if kind != "run":
            records[m["id"]] = mt.make_record(m, src, "invalid", why or "bridge mutants must be executable", today, judge)
            mt.save_records(results_path, records); continue
        path = work / m["file"]; fixed = path.read_bytes(); old, new = m["old"].encode(), m["new"].encode()
        if fixed.count(old) != 1 or judge != oracle_hash(m, work):
            raise RuntimeError("bridge source/judge differs before mutation")
        evidence = {"schema": "geometry-bridge-mutation-execution/1", "head": head, "platform": os.name,
                    "tool_sha256": mt.tool_hash(), "oracle_sha256": judge, "methods": m["tests"], "restored_methods": RESTORED,
                    "baseline_build": baseline_build, "baseline_identity": baseline_identity, "baseline": baseline}
        verdict, reason = "blocked", "not executed"
        try:
            path.write_bytes(fixed.replace(old, new, 1))
            b, identity = _build(work, folder / "bridge-mutant", env, folder, "mutant-build", root, cache)
            evidence.update(mutant_build=b, mutant_identity=identity)
            trial = _test(work, folder / "bridge-mutant" / binary_name, m["tests"], env, folder, "mutant", root, cache)
            evidence["mutant"] = trial
            if _identity(work, folder / "bridge-mutant") != identity or oracle_hash(m, work) != judge or mt.tool_hash() != evidence["tool_sha256"]:
                raise RuntimeError("bridge source/binary/judge changed during oracle")
            verdict = classify(trial, m["tests"]); reason = "actual explicit bridge unittest outcome"
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            verdict, reason = "blocked", str(exc)
        finally:
            path.write_bytes(fixed); evidence["byte_restored"] = path.read_bytes() == fixed
        try:
            if mt.Sources(work).closure != src.closure:
                raise RuntimeError("bridge scratch source was not restored")
            b, identity = _build(work, folder / "bridge-restored", env, folder, "restored-build", root, cache)
            restored = _test(work, folder / "bridge-restored" / binary_name, RESTORED, env, folder, "restored", root, cache)
            evidence.update(restored_build=b, restored_identity=identity, restored=restored)
            if (classify(restored, RESTORED) != "survived" or (os.name == "posix" and identity["exe_sha256"] != baseline_identity["exe_sha256"])
                    or _identity(work, folder / "bridge-restored") != identity or oracle_hash(m, root) != judge
                    or oracle_hash(m, work) != judge):
                raise RuntimeError("restored bridge/judge did not match baseline")
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            verdict, reason = "blocked", str(exc)
        killers = ([x["test"] for x in evidence["mutant"]["result"]["failures"]][:mt.KILLED_BY_MAX]
                   if verdict == "killed" else None)
        rec = mt.make_record(m, src, verdict, reason, today, judge, killed_by=killers, execution=evidence)
        if verdict in ("killed", "survived") and execution_problems(mt, m, rec, verdict, src):
            rec = mt.make_record(m, src, "blocked", ";".join(execution_problems(mt, m, rec, verdict, src)), today, judge, execution=evidence)
        records[m["id"]] = rec; mt.save_records(results_path, records)
        print(m["id"], rec["verdict"].upper(), m["desc"], flush=True)
    return records
