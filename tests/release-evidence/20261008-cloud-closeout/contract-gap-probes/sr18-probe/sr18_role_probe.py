#!/usr/bin/env python3
"""SR18: real support + full-cell positive control, then I21 role-only rejection.

Prepared source only; author has not run this against native. Run serially under
the root native owner. The fixture borrows existing unittest setup helpers, not
their mixed-failure oracle. It never builds a binary or connects to an HTTP app.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import traceback


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def git(root, *args):
    p = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if p.returncode:
        raise RuntimeError(f"git {args!r} failed: {p.stderr.decode(errors='replace')}")
    return p.stdout


def identity(root, out, tag, paths):
    diff = git(root, "diff", "--binary", "HEAD")
    (out / f"{tag}.diff").write_bytes(diff)
    value = {
        "at": now(), "root": str(root),
        "head": git(root, "rev-parse", "HEAD").decode().strip(),
        "main": git(root, "rev-parse", "origin/main").decode().strip(),
        "status": git(root, "status", "--short").decode(),
        "dirty_diff_sha256": digest(diff), "files": {},
    }
    for path in paths:
        blob = git(root, "show", "HEAD:" + path)
        actual = (root / path).read_bytes()
        value["files"][path] = {"sha256": digest(actual), "head_blob_sha256": digest(blob)}
        if actual != blob:
            raise RuntimeError(f"Probe/native dependency differs from HEAD: {path}")
    write_json(out / f"{tag}-identity.json", value)
    return value


def footprint_xy(geometry):
    """Independent integer AABB from serialized origin/axes and dimensions.

    Fixture placement is origin(0,0,0), u=+x,v=+y. No native evaluator is called.
    """
    origin, axes = geometry["origin"], geometry["axes"]
    dimensions = [geometry["length"], geometry["A"], geometry["B"]]
    points = [[origin[k] + sum(bits[a] * dimensions[a] * axes[a][k]
                               for a in range(3)) for k in range(3)]
              for bits in itertools.product((0, 1), repeat=3)]
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="/workspace/geometry-axiom")
    parser.add_argument("--head", required=True, help="Expected actual full Git SHA")
    parser.add_argument("--out", required=True, help="Fresh evidence directory; never overwritten")
    args = parser.parse_args()
    root, out = Path(args.repo).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"schema": "geometry-sr18-role-probe/1", "started": now(),
              "argv": sys.argv, "cwd": os.getcwd(), "python": sys.version,
              "probe_sha256": digest(Path(__file__).read_bytes()),
              "status": "not-completed", "checks": [], "limitations": [
                  "Native-only; no browser/UI, physical device or OS dialog claim.",
                  "Only role changes in the negative case; selector and all geometry remain fixed.",
                  "Explicit primary override is legal when I18-I22 hold; no rule-specific secondary-only guard is invented.",
                  "No source-parameter or binding-anchor edit (SR15) is covered.",
                  "Documentation/evidence worktree changes may exist and are recorded, never mislabeled clean.",
              ]}
    bridge = None
    timer = None
    handles = []
    before = None
    code = 1

    def check(name, condition, actual=None):
        report["checks"].append({"name": name, "passed": bool(condition), "at": now(), "actual": actual})
        if not condition:
            raise AssertionError(name)

    try:
        explicit = os.environ.get("GEOMETRY_TEST_BRIDGE")
        if not explicit:
            raise RuntimeError("GEOMETRY_TEST_BRIDGE must explicitly name a prebuilt fresh bridge; no auto-build allowed")
        sys.path[:0] = [str(root), str(root / "tests")]
        from tests import _bridge
        from tests.test_grid_subdivision_oracle import NativeSubdivisionOracle
        from tests.test_grid_system_contract import rejection_reason
        import binaries

        info = binaries.inspect_one(binaries.BY_NAME["bridge"], path=explicit)
        if info.state != "fresh":
            raise RuntimeError("Native precondition failed: " + json.dumps(info.as_dict(), ensure_ascii=False))
        binary = info.path.resolve()
        sidecar = binary.with_name(binary.name + binaries.SIDECAR_SUFFIX)
        side = json.loads(sidecar.read_text())
        paths = sorted(set(side["files"]) | {
            "公理層.md", "tests/_bridge.py", "tests/binaries.py",
            "tests/test_grid_subdivision_oracle.py", "tests/test_grid_system_contract.py",
            "tests/fixtures/grid_subdivision_vectors.json",
        })
        before = identity(root, out, "before", paths)
        if before["head"] != args.head:
            raise RuntimeError("Actual HEAD does not equal --head")
        report["before_identity"] = before
        report["bridge"] = {**info.as_dict(), "fingerprint": info.fingerprint,
                            "sha256": digest(binary.read_bytes()), "sidecar_sha256": digest(sidecar.read_bytes())}
        (out / "bridge.fingerprint.json").write_bytes(sidecar.read_bytes())
        raw_in = (out / "bridge.stdin").open("w", encoding="utf-8")
        raw_out = (out / "bridge.stdout").open("w", encoding="utf-8")
        protocol = (out / "commands.jsonl").open("w", encoding="utf-8")
        handles = [raw_in, raw_out, protocol]

        class RecordedBridge(_bridge.BridgeSession):
            def command(self, command):
                stamp = now()
                raw_in.write(command + "\n"); raw_in.flush()
                self.process.stdin.write(command + "\n"); self.process.stdin.flush()
                line = self.process.stdout.readline()
                raw_out.write(line); raw_out.flush()
                if not line:
                    raise AssertionError("Bridge closed while awaiting response: " + self.stderr_text())
                result = json.loads(line)
                protocol.write(json.dumps({"at": stamp, "command": command, "response": result}, ensure_ascii=False) + "\n")
                protocol.flush()
                return result

        bridge = RecordedBridge(str(binary), cwd=out)
        report["bridge"]["pid"] = bridge.process.pid
        proc_exe = Path(f"/proc/{bridge.process.pid}/exe")
        if proc_exe.exists():
            report["bridge"]["loaded_executable"] = os.readlink(proc_exe)
            report["bridge"]["loaded_sha256"] = digest(proc_exe.read_bytes())
            check("launched native process bytes match the inspected bridge", report["bridge"]["loaded_sha256"] == report["bridge"]["sha256"])
        else:
            report["bridge"]["loaded_sha256"] = None
            report["limitations"].append("No /proc executable hash available; configured binary hash and direct child invocation only.")

        def timeout():
            report["timed_out"] = True
            if bridge.process.poll() is None:
                bridge.process.kill()  # Only this probe's own fresh child.

        timer = threading.Timer(90, timeout); timer.daemon = True; timer.start()
        case = NativeSubdivisionOracle("test_direct_line_needs_real_support_and_complete_cell_scope_while_guide_is_coordinate_only")
        case.session = bridge
        case.commit("reset")
        # Fixture change only: full-height parent cell eliminates the original
        # 400mm-cell/1560mm-span confound. Rule divisions remain (3,2).
        case.commit(case.source(v="repeat 0 1600"))
        case.commit(case.rule())
        case.boundary()
        case.binding()
        case.apply_grid()
        case.real_supports()
        refs = case.command("references")
        supports = {row["id"]: row for row in refs["timbers"]}
        check("real boundary supports and existing legal primaries are placed", all(
            supports[i]["role"] == role and supports[i].get("geometry") is not None
            for i, role in ((81, "boundary"), (82, "boundary"), (1, "primary"), (2, "primary"))))
        check("existing primary axis and literal supported lengths are v/1560", all(
            supports[i]["geometry"]["dir"] == "+v" and supports[i]["geometry"]["length"] == 1560 for i in (1, 2)))
        cell = case.query("grid", 10, cell=("-2", "1"))
        check("queried formal source-rule cell has literal complete bounds", cell.get("ok") and cell.get("bounds") == [100, 200, 700, 1800], cell)
        line = next(x for x in cell["lines"] if x["axis"] == "u" and x["innerIndex"] == 0)
        check("formal u0 line is at x300 with full identity", line["coordinate"] == 300 and line["ref"] == {
            "kind": "grid-rule-line", "appliedGridId": 10, "systemId": 0, "ruleKey": 1,
            "cellI": "-2", "cellJ": "1", "axis": "u", "innerIndex": 0}, line)

        anchor = "at-line rule 10 0 1 -2 1 u 0"
        selector = "between t81 t82"
        case.commit("timber 9 20 20 role primary")
        case.commit(f"place 9 on 1 {anchor} {selector} +v +n")
        target = case.timber(9)
        write_json(out / "positive-target.json", target)
        geometry = target["geometry"]
        check("positive primary override uses the exact rule anchor and real support selector",
              target["role"] == "primary" and target["definition"]["anchor"] == anchor
              and target["definition"]["selector"] == selector, target)
        check("positive direct-rule primary has literal x300 length1560 section20x20",
              geometry["centerline"] == 300 and geometry["length"] == 1560
              and geometry["A"] == geometry["B"] == 20 and geometry["dir"] == "+v", geometry)
        footprint = footprint_xy(geometry)
        check("complete supported footprint is exactly inside parent cell", footprint == [290, 220, 310, 1780]
              and 100 <= footprint[0] < footprint[2] <= 700 and 200 <= footprint[1] < footprint[3] <= 1800, footprint)

        def snapshot():
            dump = case.command("dump")
            references = case.command("references")
            assembly = case.command("assembly-read")
            if not dump.get("ok") or not references.get("ok") or not assembly.get("ok"):
                raise AssertionError("Snapshot read failed")
            return {"dump": dump["text"], "references": references,
                    "revision": assembly["revision"], "definition_sha256": assembly["definition_sha256"]}

        previous = snapshot()
        write_json(out / "before-role-change.json", previous)
        # The ONLY attempted product change: declared primary -> secondary.
        # Same id, A/B, placement, formal rule tuple, selector, direction/supports.
        response = case.line("timber 9 20 20 role secondary")
        write_json(out / "role-rejection.json", response)
        reason = rejection_reason(response)
        check("role-only edit is refused", not (response.get("ok") and response.get("preview", {}).get("valid", True)), response)
        check("refusal pins D17/I21 V_PRIMARY_AXIS for timber9 secondary, not local-span or missing support",
              "V_PRIMARY_AXIS" in reason and "secondary" in reason and "角材 9" in reason
              and "I13/R6" not in reason, reason)
        if "preview" in response:
            check("rejected role candidate is invalid", response["preview"]["valid"] is False)
            attempted = case.line("confirm " + str(response["preview"]["token"]))
            check("invalid role candidate cannot be confirmed", attempted.get("ok") is False, attempted)
        after_role = snapshot()
        write_json(out / "after-role-change.json", after_role)
        check("role refusal preserves complete dump/references/revision/definition hash", after_role == previous)
        check("original primary and exact formal selector remain", case.timber(9) == target)
        report["status"] = "passed"
        code = 0
    except BaseException as error:
        report["status"] = "failed" if report["checks"] else "blocked-precondition"
        report["error"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
        print(traceback.format_exc(), file=sys.stderr)
    finally:
        if timer:
            timer.cancel()
        if bridge:
            try:
                bridge.process.stdin.close()
                try:
                    bridge.process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    bridge.process.kill(); bridge.process.wait(timeout=5)
                    report["cleanup_forced_kill"] = True
                    code = 1
                report["bridge"]["exit_code"] = bridge.process.returncode
                bridge.stderr.seek(0)
                (out / "bridge.stderr").write_bytes(bridge.stderr.read())
                bridge.stderr.close(); bridge.process.stdout.close(); bridge._stopped = True
                if bridge.process.returncode != 0:
                    code = 1
            except BaseException as error:
                report["cleanup_error"] = repr(error)
                code = 1
        for handle in handles:
            handle.close()
        if before:
            try:
                after = identity(root, out, "after", list(before["files"]))
                report["after_identity"] = after
                check("Git head and probe/native dependency bytes remain identical",
                      after["head"] == before["head"] and after["files"] == before["files"])
            except BaseException as error:
                report["post_identity_error"] = repr(error)
                code = 1
        if code:
            report["status"] = "failed" if report["checks"] else "blocked-precondition"
        report["finished"] = now()
        report["exit_code"] = code
        write_json(out / "result.json", report)
        write_json(out / "artifacts.json", [{"path": str(p.relative_to(out)), "bytes": p.stat().st_size,
                                           "sha256": digest(p.read_bytes())}
                                          for p in sorted(out.rglob("*")) if p.is_file() and p.name != "artifacts.json"])
        print(json.dumps({"status": report["status"], "exit_code": code, "out": str(out)}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
