"""Named 0/1/0 X2 withdrawals in isolated Node module loaders, with bounded waits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "geometry-web/project-store.js"
TEST = "tests/test_project_save_compat.js"
GUARD = '''    // An explicit version must be readable before normalization can select an
    // output format. Inspect the descriptor without invoking an input getter.
    const declaredFormat = Object.getOwnPropertyDescriptor(manifest, "format");
    if (declaredFormat) {
      if (!Object.hasOwn(declaredFormat, "value")) fail("專案資料欄位不合法。");
      formatPolicy(declaredFormat.value);
    }
'''


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise AssertionError("X2_MUTATION_ANCHOR: expected one exact occurrence")
    return source.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    source = SOURCE.read_text(encoding="utf-8")
    inputs = [SOURCE, ROOT / TEST, ROOT / "tests/fixtures/project-save-history.json"]
    input_hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    cases = [
        ("remove-version-guard", "X2_FUTURE_ORIGINAL_WRITE_REFUSED", "X2_FUTURE_WRITE_REFUSED",
         replace_once(source, GUARD, "")),
        ("invoke-format-getter", "X2_FORMAT_ACCESSOR_NOT_INVOKED", "X2_FORMAT_ACCESSOR_NOT_INVOKED",
         replace_once(source, GUARD, '    if (Object.hasOwn(manifest, "format")) formatPolicy(manifest.format);\n')),
        ("delete-explicit-undefined", "X2_UNKNOWN_FORMAT_WRITE_REFUSED", "X2_EXPLICIT_UNDEFINED_FORMAT:INPUT_UNCHANGED",
         replace_once(source, '      formatPolicy(declaredFormat.value);',
                      '      if (declaredFormat.value === undefined) delete manifest.format;\n      formatPolicy(declaredFormat.value);')),
        ("rewrite-manifest-value", "X2_HISTORY_canvas-1_ENTRY_BYTES", "X2_ENTRY_BYTES:canvas-1:manifest.json",
         replace_once(source, 'const manifestBytes = new TextEncoder().encode(JSON.stringify(m));',
                      'const manifestBytes = new TextEncoder().encode(JSON.stringify({...m, name:m.name + " changed"}));')),
        ("upgrade-unknown-generator", "X2_UNKNOWN_GENERATOR_PRESERVED_READONLY", "X2_ENTRY_BYTES:unknown-generator:manifest.json",
         replace_once(source, 'const manifestBytes = new TextEncoder().encode(JSON.stringify(m));',
                      'const manifestBytes = new TextEncoder().encode(JSON.stringify(m, (key,value) => key === "version" && value === 999 ? 1 : value));')),
        ("drop-source-member", "X2_HISTORY_canvas-9_ENTRY_BYTES", "X2_ENTRY_SET:canvas-9",
         replace_once(source, 'zip.zip(entries, { level: 0 },',
                      'zip.zip(Object.fromEntries(Object.entries(entries).filter(([name]) => !name.startsWith("sources/"))), { level: 0 },')),
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix="x2-withdrawal-") as temporary:
        scratch = Path(temporary)
        candidate, hook = scratch / "candidate.js", scratch / "loader.cjs"
        hook.write_text(
            "const Module=require('node:module'),fs=require('node:fs');\n"
            "const original=Module._extensions['.js'];\n"
            "Module._extensions['.js']=function(module,filename){\n"
            "if(filename===" + json.dumps(str(SOURCE)) + ") return module._compile(fs.readFileSync("
            + json.dumps(str(candidate)) + ",'utf8'),filename);\n"
            "return original(module,filename);};\n", encoding="utf-8")
        for name, test, assertion, mutant in cases:
            exits = []
            for phase, text, expected in [("before", source, 0), ("withdrawn", mutant, 1), ("restored", source, 0)]:
                candidate.write_text(text, encoding="utf-8")
                command = ["node", "--require", str(hook), "--test", "--test-reporter=tap", "--test-name-pattern=^" + re.escape(test) + "$", TEST]
                run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=45)
                raw = run.stdout + run.stderr
                (args.out / (name + "." + phase + ".log")).write_text(raw, encoding="utf-8")
                if run.returncode != expected:
                    raise AssertionError(f"X2_WITHDRAWAL_EXIT:{name}:{phase}:{run.returncode}")
                if not re.search(r"^# tests 1$", raw, re.M):
                    raise AssertionError(f"X2_WITHDRAWAL_CENSUS:{name}:{phase}")
                if expected:
                    if not ("not ok 1 - " + test in raw and assertion in raw and "ERR_ASSERTION" in raw):
                        raise AssertionError(f"X2_WITHDRAWAL_WRONG_RED:{name}")
                elif "# fail 0" not in raw or "# skipped 0" not in raw:
                    raise AssertionError(f"X2_WITHDRAWAL_NOT_GREEN:{name}:{phase}")
                exits.append(run.returncode)
                results.append({"name": name, "phase": phase, "command": shlex.join(command),
                                "exit": run.returncode, "test": test, "requiredAssertion": assertion})
            print(name + ": " + "/".join(map(str, exits)), flush=True)
    if SOURCE.read_text(encoding="utf-8") != source:
        raise AssertionError("X2_SOURCE_CHANGED_DURING_WITHDRAWALS")
    if input_hashes != {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}:
        raise AssertionError("X2_INPUT_CHANGED_DURING_WITHDRAWALS")
    (args.out / "results.json").write_text(json.dumps({"acceptance": False, "inputSha256": input_hashes, "executions": results}, indent=2) + "\n", encoding="utf-8")
    print("X2_NAMED_WITHDRAWALS: 6 verified; product source unchanged", flush=True)


if __name__ == "__main__":
    main()
