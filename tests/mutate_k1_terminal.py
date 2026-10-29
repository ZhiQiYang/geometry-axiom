"""K1-a fault injection in disposable C sources; no checkout or expected-value edits.

python tests/mutate_k1_terminal.py [--sanitize] [--out PATH]
Only an assertion failure with a named terminal cause counts as killed.
Compiler failures, crashes, skipped tests and environmental blocks remain failures.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import binaries

CASES = [
    ("omit-engineering-field", "geometry-web/engineering_bridge.inc",
     'fputs(",\\\"terminal\\\":",stdout);json_eng_terminal(resolved?&terminal:NULL);', '',
     "test_n2_application_material_and_gap_literal"),
    ("omit-slot-field", "geometry-web/assembly_bridge.inc",
     'fputs(",\\\"terminal\\\":",stdout);json_eng_terminal(&terminal);', '',
     "test_n4_owned_slot_effective_material_leaf"),
    ("wrong-application-leaf", "geometry-templates/woodworking/native/engineering.c",
     'if(terminal&&s->kind!=ENG_APPLICATION)', 'if(terminal)',
     "test_n2_application_material_and_gap_literal"),
    ("wrong-material-fingerprint", "geometry-templates/woodworking/native/engineering.c",
     'snprintf(terminal->fingerprint,sizeof terminal->fingerprint,"%s",m->fingerprint);',
     'memset(terminal->fingerprint,\'0\',64);terminal->fingerprint[64]=0;',
     "test_n1_literal_spec_parameter_and_material_leaves"),
    ("wrong-override-leaf", "geometry-templates/woodworking/native/engineering.c",
     'b->has_override?&b->override_value:&b->source,&b->target,pid,role,value,path,cap,terminal',
     '&b->source,&b->target,pid,role,value,path,cap,terminal',
     "test_n3_face_and_object_overrides_replace_the_terminal"),
    ("missing-unresolved-null", "geometry-web/engineering_bridge.inc",
     'json_eng_terminal(resolved?&terminal:NULL)', 'if(resolved)json_eng_terminal(&terminal);else fputs("{\\\"kind\\\":\\\"literal\\\"}",stdout)',
     "test_n5_invalid_preview_returns_null_without_mutating_world"),
]


def killed_by_named_assertion(code, log, method):
    return (code == 1 and "AssertionError" in log and
            re.search(r"^FAIL: " + re.escape(method) + r"\s", log, re.M) is not None and
            "errors=" not in log and "skipped" not in log and
            "AddressSanitizer" not in log and "runtime error:" not in log and
            "BridgeClosed" not in log and "Segmentation fault" not in log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sanitize", action="store_true")
    parser.add_argument("--out", type=Path, default=Path(tempfile.gettempdir()) / "geometry-tests/k1-terminal-mutations.json")
    args = parser.parse_args()
    if args.sanitize and os.name == "nt":
        parser.error("ASan/UBSan requires the Linux/WSL compiler")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="k1-terminal-mutations-") as directory:
        source = Path(directory)
        source_hashes = {}
        for parent in (ROOT, ROOT / "geometry-core", ROOT / "geometry-web", ROOT / "geometry-app", ROOT / "geometry-templates"):
            paths = parent.iterdir() if parent == ROOT else parent.rglob("*")
            for path in paths:
                if path.is_file() and path.suffix in (".c", ".h", ".inc") and "vendor" not in path.parts:
                    target = source / path.relative_to(ROOT)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
                    source_hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        binaries.ROOT = source
        for name, filename, before, after, method in [("baseline", "", "", "", ""), *CASES]:
            target = source / filename if filename else None
            if target:
                original = target.read_bytes()
                if original.count(before.encode()) != 1:
                    raise RuntimeError(name + ": mutation anchor missing or nonunique")
                target.write_bytes(original.replace(before.encode(), after.encode()))
            binaries.OUT_DIR = source / ("bin-" + name)
            binaries.OUT_DIR.mkdir()
            binary = binaries.BY_NAME["bridge"]
            if args.sanitize:
                binary.posix_flags = ["-std=c11", "-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
            code, log, _ = binaries._compile(binary, source / "geometry-web/web_bridge.c")
            verdict = "compile-failed"
            if code == 0:
                env = dict(os.environ, GEOMETRY_TERMINAL_HARNESS=str(binary.path))
                env.pop("GEOMETRY_TERMINAL_BASELINE", None)
                test = "tests.test_engineering_terminal" + (".EngineeringTerminal." + method if method else "")
                for attempt in range(4):
                    run = subprocess.run([sys.executable, "-m", "unittest", test, "-v"], cwd=ROOT,
                                         env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=150)
                    log = run.stdout + run.stderr
                    if "4551" not in log or attempt == 3:
                        break
                    time.sleep(12)
                if name == "baseline":
                    verdict = "passed" if run.returncode == 0 and "skipped" not in log else "failed"
                else:
                    verdict = "killed" if killed_by_named_assertion(run.returncode, log, method) else "not-killed"
            log_path = args.out.with_name(args.out.stem + "-" + name + ".log")
            log_path.write_text(log, encoding="utf-8")
            results.append({"case": name, "verdict": verdict, "test": method,
                            "source": filename or None,
                            "mutation_sha256": hashlib.sha256((before + '\0' + after).encode()).hexdigest() if target else None,
                            "binary_sha256": hashlib.sha256(binary.path.read_bytes()).hexdigest() if binary.path.exists() else None,
                            "log": str(log_path)})
            judges = [ROOT / "tests" / name for name in ("test_engineering_terminal.py", "binaries.py", "fixtures/k1_terminal_legacy_replies.json")]
            args.out.write_text(json.dumps({"schema": "k1-terminal-mutations/1", "sources": source_hashes,
                "judges": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None for p in judges},
                "results": results}, indent=2) + '\n', encoding="utf-8")
            print(name + ": " + verdict, flush=True)
            if target:
                target.write_bytes(original)
            if name == "baseline" and verdict != "passed":
                return 1
    return 0 if all(r["verdict"] in ("passed", "killed") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
