"""Bridge-backed mutation records for guards outside the core scene oracle.

Mutants run in a separate, sparse committed checkout. The invoking repository and
its live runtime are never temporarily mutated. Every record includes baseline,
real failing unittest results, restored results, binaries and official sidecars.

Verdicts follow tests/mutate.py: only a failed test assertion is `killed`. A bridge process that died under
the test (the oracle's `bridge_closed` failure kind, with its exit status) is not an assertion: it is `crashed`
(detected, counted apart from killed) only when the same tests died of an access violation
(mutate.is_access_violation_code: 0xC0000005 either signedness, or -11) in mt.RUN_RETRIES consecutive runs and no
assertion failed; the dying run is repeated for that. Every other death (exit status 1 from an external kill,
-9/OOM, abort, Smart App Control), fewer repeats, inconsistent repeats, a death beside assertion failures,
a failure whose text says the bridge closed but carries no exit status, build or launch errors, skips, timeouts and
incomplete runs are `blocked` and are never a detection.  Both killed and crashed presuppose that the mutant's own
test methods passed in the baseline run: they must be among RESTORED (tests/mutate.py::definition_kind), which the
baseline runs and must pass completely before any mutant is judged.
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
        "test_P142_B2_LONG_OWNER_LIST_KEEPS_COMPLETE_NAMES",
        # P-142 S1: grid-system field references rebound by put-grid-system.
        "test_P142_S1_GRID_SYSTEM_FIELD_REBIND_IN_SAME_CANDIDATE",
        "test_P142_S1_REDECLARATION_WITHOUT_REBUILD_REJECTS",
        # P-142 S2 on the merged source: rebuilt card read by field and card unbind.
        "test_P142_S2_INTEGRATED_FIELD_AND_CARD_REBUILD_READS_99",
    ]],
]

# #314: baseline/restoration must run these exact judges before a verdict.
RESTORED += [
    "tests.test_geo314_ordered_facts.OrderedStaggerFacts.test_fact_bytes_order_count_revision_and_provider_tampering_are_rejected",
    "tests.test_geo314_ordered_facts.OrderedStaggerFacts.test_failed_preview_clears_evidence_and_keeps_definition_and_revision",
    "tests.test_geo314_commit_paths.Geo314CommitPaths.test_default_fixed_lines_change_alarm_preserves_the_owned_replay_route",
    "tests.test_geo261_wood_grid_application.WoodGridApplication.test_stagger_commit_decision_table_and_ordered_sources",
    *["tests.test_geo314_stagger_commit.StaggerCommit." + name for name in [
        "test_C1_new_direct_and_repeat_panel_dual_axes_reject_M1",
        "test_C3_archive_new_and_existing_second_axes_reject_M1",
        "test_C4_batch_new_and_added_second_axes_reject_M1",
        "test_L1_all_frozen_legacy_modes_load_and_dump_byte_identically",
        "test_Q3_parameter_then_same_value_unbind_survives_preview_and_confirmation",
        "test_Q3_same_final_reference_preserves_card_then_unbind_and_rebind_order",
        "test_Q3_same_final_reference_cannot_exempt_value_changing_rebind",
    ]],
]

# #318: exact typed-fact witnesses are baseline/restored judges. They do not
# claim a CLI construction path; that separate acceptance remains explicit.
RESTORED += [
    'tests.test_geo318_reading_a_native.ReadingANative.test_fixed_whole_positioning_edge_endpoint_placed_contact_and_roles',
    'tests.test_geo318_reading_a_native.ReadingANative.test_returned_features_real_rc_span_exact_width_and_collinear_faces',
    'tests.test_geo318_reading_a_native.ReadingANative.test_actual_span_between_named_source_bare_rc_and_source_failure',
    'tests.test_geo318_reading_a_native.ReadingANative.test_r6e_partial_single_full_rc_source_failure_and_collision',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def oracle_hash(m, root):
    """Conservative bridge judge closure: tests/*.py, tests/*.c,
    tests/fixtures/**/*.scene and root *.scene files, with LF-normalized bytes.

    This intentionally invalidates bridge records when any included judge or
    fixture changes. The result ledger is excluded to avoid self-hashing.
    """
    root = Path(root)
    files = sorted([*root.glob("tests/*.py"), *root.glob("tests/*.c"),
                    *root.glob("tests/fixtures/**/*.scene"), *root.glob("*.scene")])
    rows = [(p.relative_to(root).as_posix(), sha(p.read_bytes().replace(b"\r\n", b"\n"))) for p in files]
    return sha(json.dumps([m["tests"], RESTORED, rows], ensure_ascii=False, separators=(",", ":")).encode())


# What a closed bridge says in a failure's text.  Sources: tests/_bridge.py (BridgeSession.command and run_once,
# `raise BridgeClosed('bridge closed: ' + ...)`) and the hand-written copies of its line protocol, e.g.
# tests/integration/assembly_ownership_probe.py (`raise AssertionError('bridge closed: ' + ...)`).  Text can only
# lower trust, never raise it: an entry labelled "assertion" or not labelled at all (a receipt written before the
# oracle labelled failures, or by some other oracle) whose detail says the bridge closed becomes "unproven"
# (-> blocked), never killed and never crashed.  An unlabelled entry without that text keeps its old meaning (an
# assertion failure), so receipts that predate the labels and the hand-made unit fixtures stay valid.
LEGACY_BRIDGE_CLOSED_TEXT = "bridge closed:"


def failure_class(failure):
    """What one entry of a result row's `failures` proves: "assertion", "death" or "unproven".

    assertion  a test assertion failed (oracle kind "assertion"): the only thing that can kill a mutant.
    death      the bridge process died under the test (oracle kind "bridge_closed" with an integer exit status).
               Not an assertion; it can become `crashed` only through access_violation_tests() and the repeat rule.
    unproven   anything that cannot be shown to be either: a closed bridge whose exit status is unknown, an
               unrecognised kind, or an entry labelled "assertion" or unlabelled whose text says the bridge closed."""
    kind = failure.get("kind")
    if kind == "assertion" and LEGACY_BRIDGE_CLOSED_TEXT not in failure.get("detail", ""):
        return "assertion"
    if kind == "bridge_closed":
        return "death" if type(failure.get("bridge_returncode")) is int else "unproven"
    if kind is None and LEGACY_BRIDGE_CLOSED_TEXT not in failure.get("detail", ""):
        return "assertion"          # unlabelled legacy entry with no sign of a dead bridge
    return "unproven"


def failure_tests(row, wanted):
    """The `test` ids of the failures of a result row whose failure_class() is `wanted`, in report order."""
    return [f["test"] for f in row["result"]["failures"] if failure_class(f) == wanted]


def _complete_row(receipt, methods):
    """The structured result row when `receipt` is a complete, unambiguous oracle report of exactly `methods`
    (every method started and counted, no errors, skips or unexpected outcomes, well-formed failures); else None."""
    if (not methods or len(set(methods)) != len(methods)
            or type(receipt.get("exit_code")) is not int or receipt.get("timed_out")):
        return None
    row = receipt.get("result")
    if not isinstance(row, dict) or row.get("schema") != "geometry-bridge-mutation-tests/1":
        return None
    if (row.get("requested") != methods or row.get("started") != methods
            or type(row.get("total")) is not int or row["total"] != len(methods)):
        return None
    for name in ("errors", "skipped", "failures"):
        if not isinstance(row.get(name), list):
            return None
    if (row["errors"] or row["skipped"] or any(type(row.get(k)) is not int or row[k] != 0
                                             for k in ("expected_failures", "unexpected_successes"))):
        return None
    for failure in row["failures"]:
        if (not isinstance(failure, dict) or not isinstance(failure.get("test"), str)
                or not isinstance(failure.get("detail"), str) or not failure["detail"]
                or not any(failure["test"] == name or failure["test"].startswith(name + " (") for name in methods)):
            return None
    return row


def classify(receipt, methods):
    """The verdict of ONE oracle run: killed, survived or blocked (the same three as mutate.classify_test_run).

    killed    the oracle ran to completion (exit status 1) and every failure is a real test assertion.
    survived  every requested method ran and passed (exit status 0).
    blocked   anything else: build/launch/lookup errors, skips, timeouts, incomplete runs, a bridge that died
              (whatever the exit status: a single death is not yet `crashed`), and any failure list that mixes
              assertions with a death or with something unproven.  Infrastructure is never a detection.
    `crashed` needs repeated evidence; it is only produced by judge_trials()."""
    row = _complete_row(receipt, methods)
    if row is None:
        return "blocked"
    if row["failures"]:
        every_failure_is_an_assertion = all(failure_class(f) == "assertion" for f in row["failures"])
        return "killed" if every_failure_is_an_assertion and receipt["exit_code"] == 1 else "blocked"
    return "survived" if receipt["exit_code"] == 0 else "blocked"


def access_violation_tests(receipt, methods, mt=None):
    """The tests whose bridge died of an access violation, when that is the ONLY problem of this run; else None.

    Mirrors mutate.access_violation_scenes: a complete oracle report (exit status 1) whose failures are all bridge
    deaths with an access-violation exit status (mutate.is_access_violation_code, the same predicate the core uses).
    Any assertion failure beside them, any other exit status (1 from an external kill, -9, abort, SAC), unknown
    status or incompleteness gives None."""
    if mt is None:
        import mutate as mt    # tests/mutate.py owns what counts as an access violation
    row = _complete_row(receipt, methods)
    if row is None or receipt["exit_code"] != 1 or not row["failures"]:
        return None
    tests = []
    for failure in row["failures"]:
        if failure_class(failure) != "death" or not mt.is_access_violation_code(failure["bridge_returncode"]):
            return None
        if failure["test"] not in tests:
            tests.append(failure["test"])
    return tuple(tests)


def run_trials(mt, run_trial, methods):
    """Run the oracle for one mutant; repeat ONLY while it keeps dying of an access violation, at most
    mt.RUN_RETRIES runs (the core's rule).  `run_trial(n)` performs run number n (1-based); returns the receipts."""
    trials = []
    for n in range(1, mt.RUN_RETRIES + 1):
        trial = run_trial(n)
        trials.append(trial)
        if classify(trial, methods) != "blocked" or access_violation_tests(trial, methods, mt) is None:
            break
    return trials


def run_why(trial, methods, mt):
    """One oracle run in words, with its actual exit statuses: what it shows and why it is or is not a verdict."""
    outcome, code, row = classify(trial, methods), trial.get("exit_code"), _complete_row(trial, methods)
    if outcome == "killed":
        return "assertion failed in " + ", ".join(failure_tests(trial, "assertion"))
    if outcome == "survived":
        return "all %d methods passed" % len(methods)
    if trial.get("timed_out"):
        return "oracle timed out (exit status %r)" % (code,)
    result = trial.get("result")
    if row is None:
        if not isinstance(result, dict):
            return "oracle printed no structured result (exit status %r)" % (code,)
        problems = []
        for name in ("errors", "skipped"):
            items = result.get(name)
            if isinstance(items, list) and items:
                problems.append("%d %s (%s)" % (len(items), name, ", ".join(
                    str(i.get("test", "?")) if isinstance(i, dict) else "?" for i in items[:3])))
        if result.get("started") != methods:
            problems.append("started %r of the %d requested methods" % (result.get("started"), len(methods)))
        return "incomplete oracle report: %s (exit status %r)" % ("; ".join(problems) or "malformed result", code)
    parts, classes = [], [failure_class(f) for f in row["failures"]]
    for failure, status in zip(row["failures"], classes):
        kind, test = failure.get("kind"), failure["test"]
        if status == "death":
            rc = failure["bridge_returncode"]
            parts.append("bridge died in %s with exit status %d (%s)" % (
                test, rc, "an access violation" if mt.is_access_violation_code(rc) else "not an access violation"))
        elif status == "assertion":
            parts.append("assertion failed in %s" % test)
        elif kind == "bridge_closed":
            parts.append("bridge closed in %s but no exit status was observed" % test)
        elif kind in ("assertion", None):
            parts.append("failure in %s says the bridge closed, with no exit status (text only)" % test)
        else:
            parts.append("unrecognised failure kind %r in %s" % (kind, test))
    if not classes:
        parts.append("no failure reported, yet the run is not clean")
    elif set(classes) == {"assertion"}:
        parts.append("the oracle exit status contradicts a completed assertion run")
    elif "assertion" in classes:
        parts.append("an assertion failure beside a death is not a kill")
    return "%s (oracle exit status %r)" % ("; ".join(parts), code)


def judge_trials(mt, trials, methods):
    """(verdict, why, killers, crashed_on) of the oracle runs of one mutant, by tests/mutate.py's own
    verdict_from_attempts: the last run decides if it is killed or survived; otherwise `crashed` needs
    mt.RUN_RETRIES runs that all died of an access violation in the same tests; everything else is blocked,
    and its `why` lists every run with the exit statuses actually seen."""
    attempts = []
    for trial in trials:
        outcome = classify(trial, methods)
        tests = access_violation_tests(trial, methods, mt)
        attempts.append((outcome, run_why(trial, methods, mt), tests,
                         failure_tests(trial, "assertion") if outcome == "killed" else []))
    verdict, why, killers, crashed_on = mt.verdict_from_attempts(attempts)
    if verdict == "blocked":
        why = ("blocked after %d oracle run(s), not a detection: %s.  Only a run whose bridge died of an access "
               "violation is repeated, and crashed needs %d such runs in a row in the same tests" % (
                   len(attempts), " | ".join("run %d: %s" % (n, a[1]) for n, a in enumerate(attempts, 1)),
                   mt.RUN_RETRIES)) if attempts else "no oracle run"
    return verdict, why, killers, crashed_on


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
        trials = e.get("mutant_attempts") or [e["mutant"]]
        if not isinstance(trials, list) or trials[-1] != e["mutant"]:
            raise ValueError("bridge mutant_attempts must end with the recorded mutant run")
        if len(trials) > mt.RUN_RETRIES:
            raise ValueError("more bridge mutant runs than the repeat rule allows")
        if any(classify(t, m["tests"]) != "blocked" or access_violation_tests(t, m["tests"], mt) is None
               for t in trials[:-1]):
            raise ValueError("bridge mutant runs were repeated for a reason the rule does not allow")
        # run_pass labels the runs mutant, mutant-2, mutant-3 and every run prints its own elapsed time, so one
        # recorded receipt copied N times can neither carry those names nor N different outputs.
        if [t.get("stdout_file") for t in trials] != ["mutant.stdout"] + ["mutant-%d.stdout" % n for n in range(2, len(trials) + 1)]:
            raise ValueError("bridge mutant runs are not the outputs run_pass wrote, in order")
        if len({t.get("stdout_sha256") for t in trials}) != len(trials):
            raise ValueError("bridge mutant runs repeat one recorded output")
        actual, _, killers, crashed_on = judge_trials(mt, trials, m["tests"])
        equivalent_survived = (verdict == "equivalent" and actual == "survived"
                              and mt.definition_kind(m, src)[0] == "equivalent")
        if (actual != verdict and not equivalent_survived) or verdict not in ("killed", "crashed", "survived", "equivalent"):
            raise ValueError("bridge verdict contradicts actual unittest results")
        if verdict == "killed" and rec.get("killed_by") != killers[:mt.KILLED_BY_MAX]:
            raise ValueError("bridge killed_by contradicts raw assertion results")
        if verdict == "crashed" and rec.get("crashed_on") != crashed_on:
            raise ValueError("bridge crashed_on contradicts repeated access violations")
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
        for row in (e["baseline"], *trials, e["restored"], e["baseline_build"], e["mutant_build"], e["restored_build"]):
            for key in ("stdout_sha256", "stderr_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", row[key]):
                    raise ValueError("missing bridge raw output hash")
        for row, methods in [(e["baseline"], RESTORED), *[(t, m["tests"]) for t in trials], (e["restored"], RESTORED)]:
            if row["command"][2] != "tests/bridge_mutation_oracle.py" or row["command"][-len(methods):] != methods:
                raise ValueError("bridge oracle command differs from declared methods")
        if not e.get("byte_restored") or e["oracle_sha256"] != oracle_hash(m, src.root):
            raise ValueError("bridge source/oracle restoration")
        if e["platform"] == os.name:
            artifact = mt.MUT_ROOT / m["id"] / "bridge-mutant" / ("bridge.exe" if os.name == "nt" else "bridge")
            if artifact.exists() and sha(artifact.read_bytes()) != e["mutant_identity"]["exe_sha256"]:
                raise ValueError("bridge executable artifact changed")
    except (KeyError, TypeError, ValueError, AttributeError, OSError) as exc:
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
        if kind not in ("run", "equivalent"):
            records[m["id"]] = mt.make_record(m, src, "invalid", why or "bridge mutants must be executable", today, judge)
            mt.save_records(results_path, records); continue
        path = work / m["file"]; fixed = path.read_bytes(); old, new = m["old"].encode(), m["new"].encode()
        if fixed.count(old) != 1 or judge != oracle_hash(m, work):
            raise RuntimeError("bridge source/judge differs before mutation")
        evidence = {"schema": "geometry-bridge-mutation-execution/1", "head": head, "platform": os.name,
                    "tool_sha256": mt.tool_hash(), "oracle_sha256": judge, "methods": m["tests"], "restored_methods": RESTORED,
                    "baseline_build": baseline_build, "baseline_identity": baseline_identity, "baseline": baseline}
        verdict, reason, judged_killers, judged_crashed_on = "blocked", "not executed", [], []
        try:
            path.write_bytes(fixed.replace(old, new, 1))
            b, identity = _build(work, folder / "bridge-mutant", env, folder, "mutant-build", root, cache)
            evidence.update(mutant_build=b, mutant_identity=identity)
            trials = run_trials(mt, lambda n: _test(work, folder / "bridge-mutant" / binary_name, m["tests"], env, folder,
                                                    "mutant" if n == 1 else "mutant-%d" % n, root, cache), m["tests"])
            evidence["mutant"] = trials[-1]
            if len(trials) > 1:
                evidence["mutant_attempts"] = trials
            if _identity(work, folder / "bridge-mutant") != identity or oracle_hash(m, work) != judge or mt.tool_hash() != evidence["tool_sha256"]:
                raise RuntimeError("bridge source/binary/judge changed during oracle")
            verdict, reason, judged_killers, judged_crashed_on = judge_trials(mt, trials, m["tests"])
            if verdict in ("killed", "survived"):
                reason = "actual explicit bridge unittest outcome"
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
        if kind == "equivalent" and verdict == "survived":
            verdict, reason = "equivalent", why
        elif kind == "equivalent" and verdict != "blocked":
            verdict, reason = "invalid", "current execution contradicts equivalence proof: " + reason
        killers = judged_killers[:mt.KILLED_BY_MAX] if verdict == "killed" else None
        crashed_on = judged_crashed_on if verdict == "crashed" else None
        rec = mt.make_record(m, src, verdict, reason, today, judge, killed_by=killers, crashed_on=crashed_on, execution=evidence)
        if verdict in ("killed", "crashed", "survived", "equivalent") and execution_problems(mt, m, rec, verdict, src):
            rec = mt.make_record(m, src, "blocked", ";".join(execution_problems(mt, m, rec, verdict, src)), today, judge, execution=evidence)
        records[m["id"]] = rec; mt.save_records(results_path, records)
        print(m["id"], rec["verdict"].upper(), m["desc"], flush=True)
    return records
