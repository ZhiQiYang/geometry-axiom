"""Read downloaded evidence only; execute no repository code or binaries."""
import ast
import hashlib
import math
import json
import re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
EXTRACTED = ROOT / "extracted"
SOURCE = Path("/tmp/geometry-pr340-20261102")
MERGE = "fc1c9f565a2e15660e931b3884dca2220cb1b7b2"
HEAD = "b3a248607d7eb68d3167abbb926cf491d9b35a26"
inputs = {}
checks = 0


def raw(path):
    body = path.read_bytes()
    name = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    inputs[name] = hashlib.sha256(body).hexdigest()
    return body.decode("utf-8")


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw(path), object_pairs_hook=unique)


def require(value, message):
    global checks
    checks += 1
    if not value:
        raise ValueError(message)


expected = load(SOURCE / 'tests/run_all.expected.json')['suites']
timing_document = load(SOURCE / 'tests/native_shard_timings.json')
timings = timing_document['timings_ms']
expected_digest = hashlib.sha256((SOURCE / 'tests/run_all.expected.json').read_bytes().replace(b'\r\n', b'\n')).hexdigest()
timings_digest = hashlib.sha256((SOURCE / 'tests/native_shard_timings.json').read_bytes().replace(b'\r\n', b'\n')).hexdigest()
module = ast.parse(raw(SOURCE / 'tests/run_all.py'))
assignments = {node.targets[0].id: node.value for node in module.body if isinstance(node, ast.Assign)
               and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
py_needs = ast.literal_eval(assignments['PY_NEEDS'])
document_nodes = ast.literal_eval(assignments['NODE_DOCUMENT_SCRIPT_FILES'])
pure_nodes = ast.literal_eval(assignments['NODE_PURE_TEST_FILES'])
registry = ['c:integrity', 'core:run_tests', 'mutation:check', 'oracle:framing-selftest']
registry += ['py:' + name for name in sorted(py_needs) if (SOURCE / 'tests' / (name + '.py')).is_file()]
registry += ['node:tests-js', 'node:model_viewer', 'node:polydraft', 'node:canvas_direct']
registry += list(document_nodes) + list(pure_nodes)
require(set(expected) == set(registry) and len(registry) == len(set(registry)), 'current static registry exact expected')
owners, loads = {}, [0, 0, 0]
for name in sorted(registry, key=lambda name: (-timings.get(name, 1000), name)):
    index = min(range(3), key=lambda index: (loads[index], index))
    owners[name] = index
    loads[index] += timings.get(name, 1000)
planned = [[name for name in registry if owners[name] == index] for index in range(3)]
raw(SOURCE / 'tests/native_shards.py')
raw(SOURCE / 'tests/native_shard_receipts.py')
pr = load(ROOT / 'api/20261102T033519Z/pr340.json')
require(pr['head']['sha'] == HEAD and pr['merge_commit_sha'] == MERGE, 'official PR head and execution merge')
jobs = load(ROOT / "api/20261102T033519Z/integration-jobs.json")["jobs"]
browser = []
for job in jobs:
    if not job["name"].startswith("browser") or job["conclusion"] != "success":
        continue
    logfile = ROOT / "job-logs" / (str(job["id"]) + ".txt")
    text = raw(logfile)
    lines = [line.partition("Z ")[2] for line in text.splitlines()]
    require(MERGE in lines, job["name"] + " checkout merge SHA")
    require(any("Merge " + HEAD + " into " in line for line in lines), job["name"] + " PR head merge parent")
    require(not any("##[error]" in line for line in lines), job["name"] + " GitHub error")
    require(any(step["name"] == "Run actual browser regression group" and step["conclusion"] == "success"
                for step in job["steps"]), job["name"] + " actual browser step success")
    runtime = [json.loads(line) for line in lines if line.startswith('{"schema": "geometry-runtime/1"')]
    require(len(runtime) == 1 and runtime[0]["fresh"] is True, job["name"] + " fresh runtime")
    markers = [(number, line.split(" ", 1)[0], json.loads(line.split(" ", 1)[1]))
               for number, line in enumerate(lines, 1)
               if line.startswith(("CDP_RESULT {", "SPACE_RESULT {", "DOCUMENTS_RESULT {"))]
    require(len(markers) == 1, job["name"] + " unique result")
    number, marker, result = markers[0]
    passed = result.get("passedAssertions", result.get("passed"))
    failed = result.get("failedAssertions", result.get("failed"))
    actual_lines = sum(line.startswith("PASS ") for line in lines) or sum(" ✓ " in line for line in lines)
    canvas_details = None
    if job["name"] == "browser (canvas)":
        # Legacy full-mode lines can carry multiple controlled verdict arguments.
        # Visible status text and JSON diagnostic strings are not verdicts (cdp_test.js:29-42).
        section = None
        raw_sections = {}
        for line in lines:
            if line.startswith("CDP_SECTIONS "):
                break
            if line.startswith("==="):
                match = re.match(r"^===\s*(?:(Setup|BF\d+|\d+)|(P\d+)([A-Z])?)", line)
                if match:
                    section = match[1] or (match[2] + match[3] if match[2] == "P72" and match[3] == "B" else match[2])
                    raw_sections.setdefault(section, 0)
            if section is None or line.startswith(("status:", "[console]", "[EXCEPTION]")):
                continue
            line = re.sub(r'"(?:\\.|[^"\\])*"', '""', line)
            if line.startswith("undo×1("):
                line = line.split("|", 1)[0]  # The trailing st1 argument is displayed status, not explicitVerdict.
            raw_sections[section] += line.count("✓")
        require(raw_sections == result["sections"], "canvas raw controlled verdicts equal every section")
        actual_lines = sum(raw_sections.values())
        golden = load(SOURCE / "geometry-web/cdp_sections.golden.json")
        require(result["scope"]["mode"] == "full" and result["scope"]["filters"] == result["scope"]["modifiers"] == []
                and result["goldenCompare"] == "matched" and golden["sections"] == raw_sections
                and golden["total"] == actual_lines and len(raw_sections) == len(golden["sections"]), "canvas exact full golden")
        expected_exceptions = [line for line in lines if line.startswith("[EXPECTED EXCEPTION]")]
        require(expected_exceptions == ["[EXPECTED EXCEPTION] Error: fb-auto-probe"]
                and not any(line.startswith("[UNEXPECTED EXCEPTION]") for line in lines)
                and result["uncaughtBrowserExceptions"] == 1, "canvas one deliberately injected P38 exception")
        source = raw(SOURCE / "geometry-web/cdp_test.js")
        require("expectedException={message:'Error: fb-auto-probe'" in source
                and "window.__g197Mode === 'partial' && cmd === 'surfaces'" in source
                and "body?.cmd==='line spec receipt_probe 10'" in source, "canvas diagnostic fault injections exist in original source")
        require(result["firstTransportFailure"]["command"] == "surfaces"
                and "P53." in result["firstTransportFailure"]["step"]
                and "receipt_probe" in result["firstNetworkFailure"]["postData"]
                and result["firstNetworkFailure"]["errorText"] == "net::ERR_ABORTED"
                and result["firstNetworkFailure"]["canceled"] is True, "canvas retained fault-injection transport diagnostics")
        canvas_details = dict(raw_section_counts=raw_sections, golden=golden,
                              expected_exceptions=expected_exceptions, unexpected_exceptions=0)
    require(passed == actual_lines and failed == 0 and passed > 0, job["name"] + " raw assertion count")
    require(not any(re.match(r"^(FAIL |ERROR|Unhandled|Error:|AssertionError|SKIP|SKIPPED)", line)
                    for line in lines), job["name"] + " failure/skip output")
    if marker == "CDP_RESULT":
        require(result["completed"] is True and result["skipped"] == []
                and result["uncaughtBrowserExceptions"] == (1 if canvas_details else 0), job["name"] + " CDP completeness")
        require(sum(result["sections"].values()) == passed, job["name"] + " section sum")
    if marker == "SPACE_RESULT":
        require(result["completed"] is True and result["completenessProblems"] == []
                and result["exceptions"] == [] and result["consoleErrors"] == [], job["name"] + " space completeness")
        require(sum(group["passed"] for group in result["groups"].values()) == passed, job["name"] + " group sum")
        require(all(group["completed"] and group["expected"] == group["passed"] and group["failed"] == 0
                    for group in result["groups"].values()), job["name"] + " group floors")
    browser.append(dict(name=job["name"], id=job["id"], marker=marker, line=number,
                        passed=passed, failed=failed, step_conclusion="success",
                        result=result, runtime=runtime[0], canvas_details=canvas_details))
pending_browser = [dict(name=job['name'], id=job['id'], status=job['status'], conclusion=job['conclusion']) for job in jobs
                   if job['name'].startswith('browser') and job['conclusion'] != 'success']
require(len(browser) + len(pending_browser) == 6, 'six browser jobs accounted')
require(all(job['status'] in ('queued', 'in_progress') and job['conclusion'] is None for job in pending_browser),
        'unfinished browser remains pending without failed conclusion')

all_rows = []
selected = []
universes = []
native = []
python_count = 0
node_count = 0
for shard in (1, 2, 3):
    part = load(EXTRACTED / f"native-shard-{shard}/shard-{shard}.json")
    folder = EXTRACTED / f"native-logs-{shard}"
    require(part['schema'] == 'geometry-native-shard/1' and part['shard'] == [shard, 3]
            and part['expected_sha256'] == expected_digest and part['timings_sha256'] == timings_digest
            and part['universe'] == registry and part['selected'] == planned[shard-1]
            and math.isfinite(part['seconds']) and 0 <= part['seconds'] < 1200,
            f'native {shard} exact source plan and source hashes')
    require(part["commit_sha"] == MERGE and part["exit_code"] == 0, f"native {shard} source/exit")
    require(part["registry_errors"] == part["expected_problems"] == [], f"native {shard} registry")
    require(Counter(part["selected"]) == Counter(row["name"] for row in part["rows"]), f"native {shard} selected/rows")
    universes.append(part["universe"])
    selected.extend(part["selected"])
    all_rows.extend(part["rows"])
    for row in part["rows"]:
        name = row["name"]
        require(row["ran"] and row["process_exit_code"] == 0 and row["failed"] == 0
                and not row["env_problem"] and not row["crashed"] and not row["expected_problem"], name + " outcome")
        require(row["skipped"] == row["allowed_skips"], name + " unexpected skip")
        require((row['counted'] and expected[name]['mode'] == 'count' and row['total'] == expected[name]['count']
                 and row['passed'] + row['skipped'] == row['total'])
                or (not row['counted'] and expected[name]['mode'] == 'exit-code-only' and row['total'] == 0
                    and row['passed'] == (0 if name == 'mutation:check' else 1)), name + ' current expected count')
        stem = name.replace(":", "_")
        output = raw(folder / (stem + ".log"))
        if name.startswith("py:"):
            python_count += 1
            receipt = load(folder / (stem + ".json"))
            unittest = raw(folder / (stem + ".unittest.log"))
            matches = re.findall(r"Ran (\d+) tests? in ", unittest)
            require(len(matches) == 1 and int(matches[0]) == receipt["run"] == receipt["total"] > 0,
                    name + " raw unittest count")
            require(all(row[field] == receipt[field] for field in ("total", "passed", "failed", "skipped")), name + " row/receipt")
            require(not any(receipt.get(field) for field in ("failed", "unrun_skipped", "blocked_by_error", "expected_failed",
                                                            "failures", "import_error", "extra_errors")), name + " receipt failure fields")
            require(not re.search(r"FAILED|Traceback|ERROR:", unittest)
                    and re.search(r"^OK(?: \(skipped=1\))?\s*$", unittest, re.M), name + " unittest OK")
            if receipt["skipped"]:
                require(name == "py:test_gdi_contract" and receipt["skipped"] == 1
                        and receipt["skip_reasons"] == {"requires compiled Windows GDI contract harness": 1}, name + " allowed GDI skip")
        elif name.startswith("node:"):
            node_count += 1
            counts = {key: [int(n) for n in re.findall(r"^.*?ℹ " + key + r" (\d+)\s*$", output, re.M)]
                      for key in ("tests", "pass", "fail", "skipped")}
            if row["counted"] and name != "node:canvas_direct":
                require(all(len(values) == 1 for values in counts.values()), name + " unique Node count markers")
                require(counts["tests"][0] == row["total"] and counts["pass"][0] == row["passed"]
                        and counts["fail"][0] == counts["skipped"][0] == 0, name + " raw Node counts")
            elif name == "node:canvas_direct":
                require(re.findall(r"(\d+) pass / (\d+) fail", output) == [(str(expected[name]["count"]), "0")]
                        and row["total"] == row["passed"] == expected[name]["count"], name + " raw direct-canvas count")
            else:
                require("passed" in output and row["total"] == 0 and row["passed"] == 1,
                        name + " explicitly exit-only suite")
        elif name == "c:integrity":
            require(output.startswith(str(expected[name]["count"]) + "/" + str(expected[name]["count"]) + " integrity checks passed") and row["total"] == row["passed"] == expected[name]["count"], name + " C count")
        elif name == "core:run_tests":
            markers = [json.loads(line.split(" ", 1)[1]) for line in output.splitlines() if line.startswith("GEOMETRY_TEST_RESULT ")]
            require(len(markers) == 1, name + " unique core result")
            result = markers[0]
            require(result["total"] == row["total"] == expected[name]["count"] and result["counts"] == {"pass": expected[name]["count"], "fail": 0, "infrastructure": 0}
                    and len(result["cases"]) == expected[name]["count"] and all(case["status"] == "pass" for case in result["cases"]), name + " core counts")
        elif name == "mutation:check":
            require("變異表 123 筆,紀錄 123 筆" in output and "過期 stale 0 / 受阻 blocked 0" in output,
                    name + " historical strict ledger result")
        elif name == "oracle:framing-selftest":
            require("掃描 8137 次建構(CI 抽樣)" in output and output.rstrip().endswith("不可施工或檢查失敗 0 個"), name + " framing completion")
        else:
            raise ValueError("unknown native row: " + name)
    native.append(dict(shard=shard, suites=len(part["rows"]),
                       **{field: sum(row[field] for row in part["rows"] if row["counted"])
                          for field in ("total", "passed", "failed", "skipped", "allowed_skips")}))
require(all(universe == universes[0] for universe in universes), "identical shard universe")
require(len(selected) == len(set(selected)) == len(registry) and set(selected) == set(universes[0]), "native exact once union")
summary = load(EXTRACTED / "native-complete-coverage/native-complete.json")
require(summary["commit_sha"] == MERGE and summary["suite_count"] == summary["executed_suites"] == len(registry)
        and summary["passed"] and summary["union_equals_full_registry"] and summary["overlap"] == [], "native complete summary")
for field, summary_field in (("total", "counted_tests"), ("passed", "counted_passed"), ("allowed_skips", "allowed_skips")):
    require(sum(part[field] for part in native) == summary[summary_field], "native sum " + field)

proof_folder = EXTRACTED / "native-complete-coverage/native-sharding-proof"
proof = load(proof_folder / "receipt.json")
require(proof["passed"] and proof["baseline_mutant_restored_exit"] == [0, 1, 0], "coverage proof exits")
for label, expected in (("baseline", 0), ("removed", 1), ("restored", 0)):
    receipt = load(proof_folder / (label + ".json"))
    log = raw(proof_folder / (label + ".log"))
    row = next(row for row in proof["rows"] if row["label"] == label)
    require(row["exit"] == expected and receipt["tests"] == 1 and receipt["failures"] == expected
            and receipt["errors"] == receipt["skips"] == 0 and all(row[key] == value for key, value in receipt.items()), label + " proof raw receipt")
    require("Ran 1 test in " in log, label + " proof test count")
    if expected:
        require(receipt["removed"] == ["c:integrity"]
                and receipt["failure_ids"] == ["test_unittest_runner.NativeShardCoverage.test_partition_covers_actual_suite_registry_once"]
                and "AssertionError: Counter(" in log and "FAILED (failures=1)" in log,
                "removed suite genuine AssertionError")
    else:
        require("... ok" in log and re.search(r"^OK\s*$", log, re.M), label + " proof real OK")

native_job_logs = []
for job in jobs:
    if not job["name"].startswith("native"):
        continue
    require(job["status"] == "completed" and job["conclusion"] == "success", job["name"] + " job success")
    log = raw(ROOT / "job-logs" / (str(job["id"]) + ".txt"))
    lines = [line.partition("Z ")[2] for line in log.splitlines()]
    require(MERGE in lines and not any("##[error]" in line for line in lines), job["name"] + " actual source/error")
    if job["name"] == "native complete coverage":
        markers = [json.loads(line) for line in lines if line.startswith('{"passed": true')]
        require(summary in markers and proof in markers, "aggregate actual log equals official artifacts")
    else:
        number = int(re.search(r"\((\d)/3\)", job["name"])[1])
        part = next(part for part in native if part["shard"] == number)
        counts = [tuple(int(n) for n in match) for line in lines
                  for match in re.findall(r"合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+", line)]
        require(counts == [(part["total"], part["passed"], part["failed"], part["skipped"])], job["name"] + " actual log total")
    native_job_logs.append(dict(name=job["name"], id=job["id"], conclusion=job["conclusion"]))

report = dict(passed=True, check_count=checks, execution_commit=MERGE, pr_head=HEAD,
              browser=browser, pending_browser=pending_browser, all_browser_complete=not pending_browser, native=native, native_complete=summary,
              native_job_logs=native_job_logs,
              python_receipts_checked=python_count, node_logs_checked=node_count,
              coverage_mutation_proof=proof, input_sha256=inputs,
              scope="Read existing downloaded files only. No repository tests, binaries, source edits, network or CI dispatch.")
(OUT / "independent-native-browser-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({key: report[key] for key in ("passed", "check_count", "execution_commit", "python_receipts_checked", "node_logs_checked", "native", "pending_browser")}, ensure_ascii=False))
