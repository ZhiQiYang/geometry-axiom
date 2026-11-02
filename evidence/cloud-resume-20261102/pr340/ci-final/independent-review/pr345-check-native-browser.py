"""Read downloaded evidence only; execute no repository code or binaries."""
import ast
import hashlib
import math
import json
import re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent / 'pr345'
EXTRACTED = ROOT / "extracted"
SOURCE = Path("/tmp/geometry-pr345-20261102")
MERGE = "f75739691f4e0d8fb73e82c22074922d8766e601"
HEAD = "577b2e81967b3019352f65df5ffe6dc48eb6202f"
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
pr = load(ROOT / 'api/20261102T034113Z/pr345.json')
require(pr['head']['sha'] == HEAD and pr['merge_commit_sha'] == MERGE, 'official PR head and execution merge')
jobs = load(ROOT / "api/20261102T034113Z/integration-jobs.json")["jobs"]
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
    require(part["commit_sha"] == MERGE and part["exit_code"] == (1 if shard == 2 else 0), f"native {shard} source/exit")
    require(part["registry_errors"] == part["expected_problems"] == [], f"native {shard} registry")
    require(Counter(part["selected"]) == Counter(row["name"] for row in part["rows"]), f"native {shard} selected/rows")
    universes.append(part["universe"])
    selected.extend(part["selected"])
    all_rows.extend(part["rows"])
    for row in part["rows"]:
        name = row["name"]
        require(row["ran"] and row["process_exit_code"] == (1 if name == "mutation:check" else 0) and row["failed"] == (1 if name == "mutation:check" else 0)
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
            require("變異表 123 筆,紀錄 123 筆" in output and "過期 stale 53 / 受阻 blocked 0" in output,
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


import subprocess
import zipfile

bad_rows = [row for row in all_rows if row['failed'] or row['process_exit_code'] or row['crashed'] or row['env_problem']]
require(len(bad_rows) == 1 and bad_rows[0]['name'] == 'mutation:check' and bad_rows[0]['process_exit_code'] == 1,
        'one explicit freshness failure preserved, not a green native aggregate')
native_job_logs = []
for job in jobs:
    if not job['name'].startswith('native'):
        continue
    if job['name'] == 'native complete coverage' and job['status'] != 'completed':
        require(job['status'] in ('queued','in_progress') and job['conclusion'] is None,
                'official complete coverage remains pending in saved snapshot')
        native_job_logs.append(dict(name=job['name'],id=job['id'],status=job['status'],conclusion=None))
        continue
    expected_failure = job['name'] in ('native (2/3)', 'native complete coverage')
    require(job['status'] == 'completed' and job['conclusion'] == ('failure' if expected_failure else 'success'),
            job['name'] + ' official actual conclusion')
    log_path = ROOT / 'job-logs' / (str(job['id']) + '.txt')
    log = raw(log_path)
    lines = [line.partition('Z ')[2] for line in log.splitlines()]
    require(MERGE in lines, job['name'] + ' actual execution merge')
    if job['name'] == 'native complete coverage':
        require(any('ValueError: 分片身分／規劃／真實退出不符' in line and 'shard-2.json' in line for line in lines)
                and any('##[error]Process completed with exit code 1.' in line for line in lines),
                'official original aggregate failed at shard 2 actual exit')
    else:
        number = int(re.search(r'\((\d)/3\)', job['name'])[1])
        part = next(part for part in native if part['shard'] == number)
        counts = [tuple(int(n) for n in match) for line in lines
                  for match in re.findall(r'合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+', line)]
        require(counts == [(part['total'],part['passed'],part['failed'],part['skipped'])], job['name']+' actual log total')
        require(any('##[error]' in line for line in lines) == expected_failure, job['name']+' raw error matches conclusion')
    native_job_logs.append(dict(name=job['name'], id=job['id'], conclusion=job['conclusion']))

git = lambda *args: subprocess.check_output(['git',*args],cwd=SOURCE,text=True).strip()
require(git('rev-parse','HEAD') == HEAD and git('status','--porcelain') == '', 'current source stays fixed and clean')
tree = git('rev-parse',HEAD+'^{tree}')
parents = git('show','-s','--format=%P',MERGE).split()
require(git('rev-parse',MERGE+'^{tree}') == tree and parents == [pr['base']['sha'],HEAD], 'true merge objects same tree and parent links')
commit = load(ROOT / 'api/execution-commit.json')
require(commit['sha'] == MERGE and commit['tree']['sha'] == tree and [row['sha'] for row in commit['parents']] == parents,
        'official GitHub commit source metadata')
receipt = load(ROOT / 'native-rejection-receipt.json')
require(receipt['sourceHead'] == HEAD and receipt['executionHead'] == MERGE and receipt['tree'] == tree
        and receipt['merge_parents'] == parents and receipt['exit_code'] == 1 and receipt['expected_native_rejection'] is True,
        'parent original verifier actual exit 1 and source binding')
require(receipt['cwd'] == str(SOURCE) and receipt['env']['GIT_WORK_TREE'] == str(SOURCE), 'original verifier cwd and worktree')
metadata = Path(receipt['env']['GIT_DIR'])
metadata_head = subprocess.check_output(['git','--git-dir',str(metadata),'rev-parse','HEAD'],text=True).strip()
require(metadata_head == MERGE, 'original verifier metadata is true execution merge')
require(receipt['command'][1:3] == ['-B','tests/native_shard_receipts.py'], 'original unpatched verifier command')
for stream in ['stdout','stderr']:
    require(receipt[stream+'_sha256'] == hashlib.sha256((ROOT / ('native-reverify.'+stream)).read_bytes()).hexdigest(),
            'original verifier '+stream+' hash')
stderr = raw(ROOT / 'native-reverify.stderr')
require(receipt['failure'] in stderr and 'ValueError: 分片身分／規劃／真實退出不符' in stderr and 'shard-2.json' in stderr,
        'original verifier rejects genuine failing shard-2')
require(receipt['native_complete_summary_present'] is False and not (ROOT / 'native-reverified.json').exists()
        and not (EXTRACTED / 'native-complete-coverage/native-complete.json').exists(), 'no accepted local or official native-complete')
require(receipt['official_negative_control'] == proof, 'parent official coverage negative proof matches raw originals')

provenance = load(ROOT / 'provenance.json')
require(provenance['source'] == str(SOURCE) and provenance['source_head'] == HEAD
        and provenance['execution_head'] == MERGE and provenance['integration_run_id'] == 41382891799
        and provenance['mutation_run_id'] == 41382891805, 'parent provenance source/run binding')
for row in provenance['original_tools_and_workflow_bytes']:
    content = (SOURCE / row['path']).read_bytes()
    require(hashlib.sha256(content).hexdigest() == row['sha256'] and hashlib.sha256(content.replace(b'\r\n',b'\n')).hexdigest() == row['lf_sha256'],
            'parent original tool hash '+row['path'])
    require(subprocess.check_output(['git','show',HEAD+':'+row['path']],cwd=SOURCE) == content,
            'source original Git bytes '+row['path'])
require((SOURCE / '.github/scripts/mutation_evidence.py').resolve().parents[2] == SOURCE
        and 'ROOT = Path(__file__).resolve().parents[2]' in (SOURCE / '.github/scripts/mutation_evidence.py').read_text(),
        'original supervisor ROOT uses own source')

zip_rows = []
for kind, run_id in [('integration',41382891799),('mutation',41382891805)]:
    artifact_api = load(ROOT / ('api/20261102T034113Z/'+kind+'-artifacts.json'))
    for artifact in artifact_api['artifacts']:
        archive_path = ROOT / 'official-zips' / f"{artifact['id']}-{artifact['name']}.zip"
        require(artifact['workflow_run']['id'] == run_id and artifact['workflow_run']['head_sha'] == HEAD,
                artifact['name']+' artifact API source/run')
        require(artifact['digest'] == 'sha256:'+hashlib.sha256(archive_path.read_bytes()).hexdigest(),artifact['name']+' API ZIP digest')
        with zipfile.ZipFile(archive_path) as archive:
            require(len(archive.namelist()) == len(set(archive.namelist())),artifact['name']+' unique ZIP names')
            for info in archive.infolist():
                rel = Path(info.filename)
                require(not rel.is_absolute() and '..' not in rel.parts and (info.external_attr >> 16) & 0o170000 != 0o120000,
                        artifact['name']+' safe ZIP member')
                if not info.is_dir():
                    require(archive.read(info.filename) == (EXTRACTED / artifact['name'] / info.filename).read_bytes(),
                            artifact['name']+'/'+info.filename+' original ZIP/extracted bytes')
            if artifact['name'] == 'native-complete-coverage':
                require('native-complete.json' not in archive.namelist()
                        and set(archive.namelist()) == {'native-sharding-proof/'+name for name in ['baseline.json','baseline.log','removed.json','removed.log','restored.json','restored.log','receipt.json']},
                        'official native-complete-coverage ZIP is proof-only, no complete summary')
        zip_rows.append(dict(id=artifact['id'], name=artifact['name'], digest=artifact['digest'], run_id=run_id))

classification = load(ROOT / 'integration-failure-classification.json')
require(classification['bad_rows'] == bad_rows and classification['stale_count'] == 53
        and classification['classification'] == 'committed-mutation-ledger-stale', 'parent saved red classification matches all-native audit')
report = dict(audit_passed=True, native_accepted=False, native_registry_complete=True,
              check_count=checks, execution_commit=MERGE, pr_head=HEAD, execution_tree=tree,
              browser=browser, pending_browser=pending_browser, all_browser_complete=not pending_browser,
              native=native, native_bad_rows=bad_rows, native_job_logs=native_job_logs,
              python_receipts_checked=python_count,node_logs_checked=node_count,
              counted_tests=sum(row['total'] for row in native),counted_passed=sum(row['passed'] for row in native),
              original_verifier_actual_exit=receipt['exit_code'], original_verifier_failure=receipt['failure'],
              official_native_complete_summary_present=False, coverage_mutation_proof=proof,
              official_zips=zip_rows, input_sha256=inputs,
              scope='Read existing downloaded files and source/Git metadata only. No product suite, network or binary execution. Failing freshness row remains failed.')
(OUT / 'pr345-independent-native-browser-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:report[key] for key in ['audit_passed','native_accepted','check_count','python_receipts_checked','node_logs_checked','counted_tests','counted_passed','native_bad_rows','pending_browser']},ensure_ascii=False))
