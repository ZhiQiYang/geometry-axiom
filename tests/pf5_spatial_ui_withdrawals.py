"""Bounded, exact-named PF-5 UI withdrawals in disposable source copies.

Every case runs one genuine Node contract before/after a single product edit,
then restores the original bytes and runs the same command a third time.
Syntax/import/runtime/timeout failures never count as a killed withdrawal.
This script does not mutate the checkout or supply browser acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
FILES = ["geometry-web/panel-fill-spatial.js", "geometry-web/panel-fill-adapter.js",
         "geometry-web/panel-fill-workspace.js", "tests/test_panel_fill_spatial_ui.js"]
CASES = [
    {
        "id": "PF5_UI_WITHDRAW_ENTRY",
        "test": "PF5_UI_EXISTING_ENTRY: the shipped workspace combines native spatial output with the original source disclosure",
        "path": "geometry-web/panel-fill-workspace.js",
        "before": "${window.PanelFillSpatial?window.PanelFillSpatial.render(spatial):''}",
        "after": "",
        "marker": "PF5_UI_ENTRY_SPATIAL_SECTION_COUNT",
        "assertion_source": "assert.equal((rendered.match(/data-pf5-spatial=/g)||[]).length,1)",
        "operator": "strictEqual", "expected": {"kind": "number", "value": 1},
        "actual": {"kind": "number", "value": 0},
    },
    {
        "id": "PF5_UI_WITHDRAW_COMPONENTS",
        "test": "PF5_UI_ALL_NATIVE_LOOPS: three views paint both depths, both components and holes without a rectangle fallback",
        "path": "geometry-web/panel-fill-spatial.js",
        "before": "(f[name]?.components||[]).map((c,index)",
        "after": "(f[name]?.components||[]).slice(0,1).map((c,index)",
        "marker": "PF5_UI_ALL_NATIVE_PATH_COUNT",
        "assertion_source": "assert.equal((html.match(/<path data-pf5-fill=/g)||[]).length,18)",
        "operator": "strictEqual", "expected": {"kind": "number", "value": 18},
        "actual": {"kind": "number", "value": 12},
    },
    {
        "id": "PF5_UI_WITHDRAW_CANDIDATE_OWNER",
        "test": "PF5_UI_CANDIDATE_OWNER: a mismatched diagnostic before cannot masquerade as the current candidate",
        "path": "geometry-web/panel-fill-adapter.js",
        "before": "if(this.spatial?.schema&&(!spatialBefore?.schema",
        "after": "if(false&&this.spatial?.schema&&(!spatialBefore?.schema",
        "marker": "PF5_UI_CANDIDATE_OWNER_UNAVAILABLE",
        "assertion_source": "assert.equal(session.candidate.spatial.after.status,'unavailable')",
        "operator": "strictEqual", "expected": {"kind": "string", "value": "unavailable"},
        "actual": {"kind": "undefined"},
    },
    {
        "id": "PF5_UI_WITHDRAW_EXACT_AREA",
        "test": "PF5_UI_EXACT_DECIMAL: display preserves integers above Number precision",
        "path": "geometry-web/panel-fill-spatial.js",
        "before": "quantity('panelArea','面材有效面積',f.panel.area,'mm²')",
        "after": "quantity('panelArea','面材有效面積',Number(f.panel.area),'mm²')",
        "marker": "PF5_UI_PANEL_AREA_EXACT_DECIMAL",
        "assertion_source": 'assert.match(html,/data-pf5-field="panelArea"[^]*?<span data-pf5-value>9007199254740993<\\/span>/)',
        "operator": "match",
        "expected": {"kind": "regexp", "source": 'data-pf5-field="panelArea"[^]*?<span data-pf5-value>9007199254740993<\\/span>', "flags": ""},
        "actual_area": "9007199254740992",
    },
]

# The reporter serializes Node test-runner event objects. A test's console output
# stays inside a test:stdout/test:stderr record, so printing a name, ERR_ASSERTION,
# or even forged JSON cannot impersonate a test:fail event.
REPORTER = r'''"use strict";
function value(v){
  if(v===undefined)return {kind:"undefined"};
  if(Object.prototype.toString.call(v)==="[object RegExp]")return {kind:"regexp",source:v.source,flags:v.flags};
  if(v===null)return {kind:"null",value:null};
  if(["string","number","boolean"].includes(typeof v))return {kind:typeof v,value:v};
  return {kind:Object.prototype.toString.call(v),value:String(v)};
}
function error(e){
  if(!e)return null;
  return {name:e.name,code:e.code,failureType:e.failureType,message:e.message,stack:e.stack,
    operator:e.operator,expected:value(e.expected),actual:value(e.actual),cause:error(e.cause)};
}
module.exports=async function*(source){
  yield JSON.stringify({type:"pf5:reporter",schema:"pf5-ui-node-events/1"})+"\n";
  let records=0;
  for await(const event of source){
    const d=event.data;let row;
    if(event.type==="test:pass"||event.type==="test:fail")row={type:event.type,data:{
      name:d.name,nesting:d.nesting,testNumber:d.testNumber,file:d.file,line:d.line,column:d.column,
      skip:d.skip,todo:d.todo,details:{type:d.details?.type,duration_ms:d.details?.duration_ms,error:error(d.details?.error)}}};
    else if(["test:summary","test:diagnostic","test:stdout","test:stderr"].includes(event.type))row={type:event.type,data:d};
    if(row){records++;yield JSON.stringify(row)+"\n";}
  }
  yield JSON.stringify({type:"pf5:reporter-end",records})+"\n";
};
'''


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def run(command, cwd, directory, tag):
    start = time.monotonic()
    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    timed_out = False
    try:
        stdout_bytes, stderr_bytes = process.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        timed_out = True
        # Node's --test may spawn a child. Kill the whole disposable process
        # group, retaining the same original 60 second bound and all raw output.
        os.killpg(process.pid, signal.SIGKILL)
        stdout_bytes, stderr_bytes = process.communicate()
    stdout = directory/(tag+".stdout.txt")
    stderr = directory/(tag+".stderr.txt")
    stdout.write_bytes(stdout_bytes)
    stderr.write_bytes(stderr_bytes)
    return {"command": command, "cwd": str(cwd), "exit": process.returncode,
            "timeout_seconds": 60, "timed_out": timed_out,
            "seconds": round(time.monotonic()-start, 6), "stdout": str(stdout), "stderr": str(stderr),
            "stdout_sha256": digest(stdout_bytes), "stderr_sha256": digest(stderr_bytes)}


def assertion_location(source, case, tree):
    text = source.decode("utf-8")
    opening = "test('"+case["test"]+"',"
    if text.count(opening) != 1:
        raise RuntimeError("PF5_UI_WITHDRAWAL_TEST: selected test must occur exactly once")
    begin = text.index(opening)
    end = text.find("\ntest(", begin+len(opening))
    end = len(text) if end == -1 else end
    if text[begin:end].count(case["assertion_source"]) != 1:
        raise RuntimeError("PF5_UI_WITHDRAWAL_MARKER: exact assertion source must occur once inside selected test")
    offset = text.index(case["assertion_source"], begin, end)+len("assert.")
    line = text.count("\n", 0, offset)+1
    column = offset-text.rfind("\n", 0, offset)
    return {"file": str(tree/"tests/test_panel_fill_spatial_ui.js"), "line": line, "column": column,
            "marker": case["marker"], "source": case["assertion_source"]}


def events(record):
    try:
        rows = [json.loads(line) for line in Path(record["stdout"]).read_text(encoding="utf-8").splitlines()]
    except (ValueError, UnicodeError) as exc:
        raise RuntimeError("PF5_UI_WITHDRAWAL_REPORTER: malformed structured output") from exc
    if (len(rows) < 2 or rows[0] != {"type": "pf5:reporter", "schema": "pf5-ui-node-events/1"}
            or rows[-1] != {"type": "pf5:reporter-end", "records": len(rows)-2}):
        raise RuntimeError("PF5_UI_WITHDRAWAL_REPORTER: complete structured reporter stream required")
    return rows[1:-1]


def selected_event(record, case, location):
    rows = events(record)
    outcomes = [row for row in rows if row["type"] in ("test:pass", "test:fail")]
    selected = [row for row in outcomes if row["data"]["name"] == case["test"]]
    filtered = [row for row in outcomes if row["data"]["name"] != case["test"]]
    if (len(selected) != 1 or selected[0]["data"].get("skip") or selected[0]["data"].get("todo")
            or any(row["type"] != "test:pass" or row["data"].get("skip") != "test name does not match pattern"
                   or row["data"].get("todo") for row in filtered)):
        raise RuntimeError("PF5_UI_WITHDRAWAL_SELECTION: exactly one active, non-skip selected test required")
    data = selected[0]["data"]
    if data.get("nesting") != 0 or data.get("file") != location["file"] or data["details"].get("type") != "test":
        raise RuntimeError("PF5_UI_WITHDRAWAL_IDENTITY: selected event must be the exact source test")
    return selected[0], rows, len(filtered)


def judge(record, case, location, expected):
    if record["timed_out"]:
        raise RuntimeError("PF5_UI_WITHDRAWAL_TIMEOUT: child exceeded the original 60 second bound")
    if record["exit"] != expected:
        raise RuntimeError("PF5_UI_WITHDRAWAL_EXIT: expected "+str(expected)+", got "+str(record["exit"]))
    outcome, rows, filtered_count = selected_event(record, case, location)
    if outcome["type"] != ("test:fail" if expected else "test:pass"):
        raise RuntimeError("PF5_UI_WITHDRAWAL_OUTCOME: selected test has the wrong outcome")
    totals = [row["data"] for row in rows if row["type"] == "test:summary" and not row["data"].get("file")]
    if len(totals) > 1:
        raise RuntimeError("PF5_UI_WITHDRAWAL_CENSUS: duplicate final summary")
    if totals:
        counts = totals[0]["counts"]
        if (counts.get("failed") != expected or counts.get("passed") != 1-expected
                or counts.get("cancelled") != 0 or counts.get("todo") != 0
                or counts.get("tests") != 1+counts.get("skipped", 0)
                or counts.get("skipped") != filtered_count):
            raise RuntimeError("PF5_UI_WITHDRAWAL_CENSUS: filtered skips are not passing contracts")
    if expected == 1:
        wrapper = outcome["data"]["details"].get("error") or {}
        cause = wrapper.get("cause") or {}
        if (wrapper.get("code") != "ERR_TEST_FAILURE" or wrapper.get("failureType") != "testCodeFailure"
                or cause.get("name") != "AssertionError" or cause.get("code") != "ERR_ASSERTION"):
            raise RuntimeError("PF5_UI_WITHDRAWAL_UNRELATED_FAILURE: a real AssertionError/ERR_ASSERTION is required")
        stack_frames = [line.strip() for line in cause.get("stack", "").splitlines() if line.lstrip().startswith("at ")]
        point = location["file"]+":"+str(location["line"])+":"+str(location["column"])
        if (cause.get("operator") != case["operator"] or cause.get("expected") != case["expected"]
                or not stack_frames or not stack_frames[0].endswith("("+point+")")
                or "actual" in case and cause.get("actual") != case["actual"]):
            raise RuntimeError("PF5_UI_WITHDRAWAL_INTENDED_ASSERTION: "+case["marker"]+" did not fail at its exact call")
        if "actual_area" in case:
            actual = cause.get("actual") or {}
            area = re.search(r'data-pf5-field="panelArea".*?<span data-pf5-value>([^<]+)</span>',
                             actual.get("value", ""), flags=re.DOTALL) if actual.get("kind") == "string" else None
            if not area or area.group(1) != case["actual_area"]:
                raise RuntimeError("PF5_UI_WITHDRAWAL_INTENDED_ASSERTION: exact decimal-loss actual value absent")
    elif outcome["data"]["details"].get("error"):
        raise RuntimeError("PF5_UI_WITHDRAWAL_BASELINE: passing selected event contains an error")
    record["judged"] = {"selected_tests": 1, "filtered_skips": filtered_count,
                        "assertion_marker": case["marker"] if expected else None}


def copy_tree(tree, original):
    for name, raw in original.items():
        destination = tree/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    (tree/"withdrawal-reporter.cjs").write_text(REPORTER, encoding="utf-8")


def test_command(node, case):
    return [node, "--test", "--test-reporter=./withdrawal-reporter.cjs",
            "--test-name-pattern=^"+re.escape(case["test"])+"$", "tests/test_panel_fill_spatial_ui.js"]


def negative_controls(node, output, original, manifest):
    # These are real executions in disposable copies, not fabricated logs or
    # regex-only tests. Neither the checkout test nor product source is edited.
    case = CASES[0]
    controls = [
        ("GENERIC_ERROR", "console.log('AssertionError ERR_ASSERTION "+case["marker"]+"');throw new Error('other')",
         "PF5_UI_WITHDRAWAL_UNRELATED_FAILURE"),
        ("WRONG_ASSERTION", "assert.equal(0,2)", "PF5_UI_WITHDRAWAL_INTENDED_ASSERTION"),
        ("TIMEOUT", "await new Promise(()=>{setInterval(()=>{},1000)})", "PF5_UI_WITHDRAWAL_TIMEOUT"),
    ]
    for name, replacement, rejection in controls:
        directory = output/("negative-"+name.lower())
        tree = directory/"tree"
        copy_tree(tree, original)
        location = assertion_location(original[FILES[-1]], case, tree)
        path = tree/FILES[-1]
        source = path.read_text(encoding="utf-8")
        if source.count(case["assertion_source"]) != 1:
            raise RuntimeError("PF5_UI_WITHDRAWAL_NEGATIVE_TARGET: scratch target must be unique")
        path.write_text(source.replace(case["assertion_source"], replacement, 1), encoding="utf-8")
        record = {"id": name, "expected_rejection": rejection, "location": location}
        manifest["negative_controls"].append(record)
        syntax = run([node, "--check", FILES[-1]], tree, directory, "syntax")
        record["syntax"] = syntax
        if syntax["timed_out"] or syntax["exit"] != 0:
            raise RuntimeError("PF5_UI_WITHDRAWAL_NEGATIVE_SYNTAX: invalid negative control cannot count")
        result = run(test_command(node, case), tree, directory, "control")
        record["run"] = result
        if name != "TIMEOUT":
            outcome, _, _ = selected_event(result, case, location)
            cause = (outcome["data"]["details"].get("error") or {}).get("cause") or {}
            if name == "GENERIC_ERROR" and (cause.get("name") != "Error" or cause.get("message") != "other"):
                raise RuntimeError("PF5_UI_WITHDRAWAL_NEGATIVE_EXECUTION: real generic Error did not execute")
            if name == "WRONG_ASSERTION" and (cause.get("code") != "ERR_ASSERTION" or cause.get("expected") != {"kind": "number", "value": 2}):
                raise RuntimeError("PF5_UI_WITHDRAWAL_NEGATIVE_EXECUTION: wrong assertion did not execute")
        elif not result["timed_out"] or result["seconds"] < 60:
            raise RuntimeError("PF5_UI_WITHDRAWAL_NEGATIVE_EXECUTION: original 60 second timeout was not exercised")
        try:
            judge(result, case, location, 1)
        except RuntimeError as exc:
            if not str(exc).startswith(rejection+":"):
                raise RuntimeError("PF5_UI_WITHDRAWAL_NEGATIVE_REASON: unexpected rejection: "+str(exc)) from exc
            record["rejected"] = str(exc)
        else:
            raise RuntimeError("PF5_UI_WITHDRAWAL_FALSE_KILL: unrelated negative control counted as a kill")
        print("PF5_UI_NEGATIVE_"+name+" rejected="+rejection, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    output = args.out.resolve()
    if output == ROOT or ROOT in output.parents or output.exists() and any(output.iterdir()):
        parser.error("--out must be a new or empty directory outside the checkout")
    output.mkdir(parents=True, exist_ok=True)
    node = shutil.which("node")
    if not node:
        parser.error("node is required; missing runtime is not an expected red")
    original = {name: (ROOT/name).read_bytes() for name in FILES}
    manifest = {"schema": "pf5-ui-withdrawals/2", "scope": "Node transport/presentation only; Chromium unrun",
                "judge": "structured Node events; exact test, AssertionError, operator, expected/actual and source call",
                "reporter_sha256": digest(REPORTER.encode()), "timeout_seconds": 60,
                "source": {name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in original.items()},
                "cases": [], "negative_controls": [], "passed": False}
    try:
        for case in CASES:
            directory = output/case["id"]
            tree = directory/"tree"
            copy_tree(tree, original)
            location = assertion_location(original[FILES[-1]], case, tree)
            record = {"id": case["id"], "test": case["test"], "assertion": location,
                      "mutation": {key: case[key] for key in ("path", "before", "after")}, "runs": []}
            manifest["cases"].append(record)
            command = test_command(node, case)
            baseline = run(command, tree, directory, "baseline")
            record["runs"].append(baseline)
            judge(baseline, case, location, 0)
            path = tree/case["path"]
            source = original[case["path"]]
            old, new = case["before"].encode(), case["after"].encode()
            if source.count(old) != 1:
                raise RuntimeError("PF5_UI_WITHDRAWAL_TARGET: product edit must match exactly once")
            try:
                path.write_bytes(source.replace(old, new, 1))
                syntax = run([node, "--check", case["path"]], tree, directory, "syntax")
                record["syntax"] = syntax
                if syntax["timed_out"] or syntax["exit"] != 0:
                    raise RuntimeError("PF5_UI_WITHDRAWAL_SYNTAX: invalid mutant cannot count")
                withdrawn = run(command, tree, directory, "withdrawn")
                record["runs"].append(withdrawn)
                judge(withdrawn, case, location, 1)
            finally:
                path.write_bytes(source)
            restored = run(command, tree, directory, "restored")
            record["runs"].append(restored)
            judge(restored, case, location, 0)
            record["restored_bytes_exact"] = all((tree/name).read_bytes() == raw for name, raw in original.items())
            if not record["restored_bytes_exact"]:
                raise RuntimeError("PF5_UI_WITHDRAWAL_RESTORE: source bytes were not restored")
            record["passed"] = True
            print(case["id"]+" 0/1/0 exact="+case["test"], flush=True)
        negative_controls(node, output, original, manifest)
        manifest["passed"] = True
    except Exception as exc:
        manifest["error"] = str(exc)
        raise
    finally:
        (output/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("PF5_UI_WITHDRAWALS "+str(output/"manifest.json"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
