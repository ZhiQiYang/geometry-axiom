"""Read downloaded evidence only; execute no repository code or binaries."""
import ast
import hashlib
import math
import json
import re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
EXTRACTED = ROOT / "extracted"
SOURCE = Path("/tmp/geometry-pr344-20261102")
MERGE = "56250470746f8a7bf6b4a235a586f2744ae3cddf"
HEAD = "503cfc59354893859ae9e6e4a6ab7c11d7972517"
inputs = {}
checks = 0


def raw(path):
    body = path.read_bytes()
    name = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    inputs[name] = hashlib.sha256(body).hexdigest()
    return body.decode("utf-8")


def strict_json(value):
    def unique(pairs):
        out = {}
        for key,item in pairs:
            if key in out:
                raise ValueError('duplicate raw marker JSON key: '+key)
            out[key]=item
        return out
    return json.loads(value,object_pairs_hook=unique)


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


current_mutants=[]
for node in ast.parse(raw(SOURCE / 'tests/mutate.py')).body:
    value=None
    if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='MUTANTS' for target in node.targets):
        value=node.value
    elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='MUTANTS':
        value=node.value
    if value is not None:
        require(isinstance(value,ast.List),'current mutation table literal list')
        for call in value.elts:
            fields={kw.arg:kw.value for kw in call.keywords}
            current_mutants.append(dict(id=ast.literal_eval(fields['id']),binary=ast.literal_eval(fields['binary'])if 'binary'in fields else 'core'))
require(len(current_mutants)==len({row['id']for row in current_mutants}),'current mutation ID uniqueness')
bridge_ids={row['id']for row in current_mutants if row['binary']=='bridge'}

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
pr = load(ROOT / 'api/20261102T050911Z/pr344.json')
require(pr['head']['sha'] == HEAD and pr['merge_commit_sha'] == MERGE, 'official PR head and execution merge')
jobs = load(ROOT / "api/20261102T050911Z/integration-jobs.json")["jobs"]
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
    runtime = [strict_json(line) for line in lines if line.startswith('{"schema": "geometry-runtime/1"')]
    require(len(runtime) == 1 and runtime[0]["fresh"] is True, job["name"] + " fresh runtime")
    markers = [(number, line.split(" ", 1)[0], strict_json(line.split(" ", 1)[1]))
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
            markers = [strict_json(line.split(" ", 1)[1]) for line in output.splitlines() if line.startswith("GEOMETRY_TEST_RESULT ")]
            require(len(markers) == 1, name + " unique core result")
            result = markers[0]
            require(result["total"] == row["total"] == expected[name]["count"] and result["counts"] == {"pass": expected[name]["count"], "fail": 0, "infrastructure": 0}
                    and len(result["cases"]) == expected[name]["count"] and all(case["status"] == "pass" for case in result["cases"]), name + " core counts")
        elif name == "mutation:check":
            require(f"變異表 {len(current_mutants)} 筆,紀錄 {len(current_mutants)} 筆" in output and f"過期 stale {len(bridge_ids)} / 受阻 blocked 0" in output,
                    name + " historical strict ledger result")
        elif name == "oracle:framing-selftest":
            require(re.search(r'掃描 ([1-9][0-9]*) 次建構\(CI 抽樣\)',output) and output.rstrip().endswith("不可施工或檢查失敗 0 個"), name + " framing completion")
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

require(len(browser)==6 and pending_browser==[],'six completed browser groups, no pending')
require({row['name']for row in browser}=={'browser ('+name+')'for name in ['assembly','documents','grid','space','timber','canvas']},
        'exact six current workflow browser groups')
bad_rows=[row for row in all_rows if row['failed'] or row['process_exit_code'] or row['crashed'] or row['env_problem'] or row['expected_problem']]
require(len(bad_rows)==1 and bad_rows[0]['name']=='mutation:check' and bad_rows[0]['process_exit_code']==1,
        'only one native freshness failure, no other assertion/error/exit failures')
raw_freshness_path=EXTRACTED/'native-logs-2/mutation_check.log'
freshness_raw=raw(raw_freshness_path)
stale_lines=[line for line in freshness_raw.splitlines()if line.startswith('  STALE ')]
stale_ids={re.search(r'STALE (M\d+)',line)[1]for line in stale_lines}
require(len(stale_lines)==len(stale_ids)==len(bridge_ids) and stale_ids==bridge_ids,
        'full original stale inventory exactly covers current bridge table')
require(all('bridge source/oracle restoration'in line for line in stale_lines),'stale restoration guard explicit for every bridge entry')
require(all('裁判已變('in line or 'equivalence audit oracle changed'in line for line in stale_lines),'stale oracle-change classification')
native_jobs=[]
for job in jobs:
    if not job['name'].startswith('native'):
        continue
    expected_fail=job['name']in ['native (2/3)','native complete coverage']
    require(job['status']=='completed' and job['conclusion']==('failure'if expected_fail else 'success'),job['name']+' official conclusion')
    path=ROOT/'job-logs'/(str(job['id'])+'.txt')
    lines=[line.partition('Z ')[2]for line in raw(path).splitlines()]
    require(MERGE in lines,job['name']+' execution merge')
    if job['name']=='native complete coverage':
        failure_lines=[line for line in lines if 'ValueError: 分片身分／規劃／真實退出不符'in line or '##[error]'in line]
        require(any('shard-2.json'in line for line in failure_lines)
                and any('##[error]Process completed with exit code 1.'in line for line in failure_lines),
                'official original aggregate rejects shard2 actual exit1')
    else:
        number=int(re.search(r'\((\d)/3\)',job['name'])[1])
        part=next(row for row in native if row['shard']==number)
        counts=[tuple(int(n)for n in match)for line in lines
                for match in re.findall(r'合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+',line)]
        require(counts==[(part['total'],part['passed'],part['failed'],part['skipped'])],job['name']+' raw counted sum')
        require(any('##[error]'in line for line in lines)==expected_fail,job['name']+' error exactly matches actual conclusion')
    native_jobs.append(dict(id=job['id'],name=job['name'],conclusion=job['conclusion']))

integration=load(ROOT/'api/20261102T050911Z/integration-run.json')
mutation=load(ROOT/'api/20261102T050911Z/mutation-run.json')
require(integration['id']==41388718270 and integration['head_sha']==HEAD and integration['run_attempt']==1
        and integration['status']=='completed' and integration['conclusion']=='failure','integration terminal failure remains failure')
require(mutation['id']==41388718083 and mutation['head_sha']==HEAD and mutation['run_attempt']==1
        and mutation['status']=='completed' and mutation['conclusion']=='success','mutation terminal API success')
require({row['name']for row in jobs if row['conclusion']=='failure'}=={'native (2/3)','native complete coverage'},'only two failed integration jobs')
git=lambda *args:subprocess.check_output(['git',*args],cwd=SOURCE,text=True).strip()
require(git('rev-parse','HEAD')==HEAD and git('status','--porcelain')=='','current source fixed and clean')
tree=git('rev-parse',HEAD+'^{tree}')
parents=git('show','-s','--format=%P',MERGE).split()
require(git('rev-parse',MERGE+'^{tree}')==tree and parents==[pr['base']['sha'],HEAD],'true merge same tree and parent linkage')
require(tree=='ff068df7b220d63e64832d3648a0b81ff8cbca57','execution source tree confirmed')
require(not(EXTRACTED/'native-complete-coverage/native-complete.json').exists(),'no accepted official native aggregate')

zip_rows=[]
for artifact in load(ROOT/'api/20261102T050911Z/integration-artifacts.json')['artifacts']:
    path=ROOT/'official-zips'/f"{artifact['id']}-{artifact['name']}.zip"
    require(artifact['workflow_run']['id']==41388718270 and artifact['workflow_run']['head_sha']==HEAD,artifact['name']+' API source/run')
    require(artifact['digest']=='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest(),artifact['name']+' official ZIP digest')
    with zipfile.ZipFile(path)as archive:
        require(len(archive.namelist())==len(set(archive.namelist())),artifact['name']+' unique ZIP members')
        for info in archive.infolist():
            rel=Path(info.filename)
            require(not rel.is_absolute() and '..'not in rel.parts and (info.external_attr >> 16)&0o170000!=0o120000,
                    artifact['name']+' safe original ZIP member')
            if not info.is_dir():
                require(archive.read(info.filename)==(EXTRACTED/artifact['name']/info.filename).read_bytes(),
                        artifact['name']+'/'+info.filename+' ZIP/extracted exact bytes')
        if artifact['name']=='native-complete-coverage':
            require('native-complete.json'not in archive.namelist(),'official aggregate ZIP contains no accepted native summary')
    zip_rows.append(dict(id=artifact['id'],name=artifact['name'],digest=artifact['digest']))
require(len(zip_rows)==12,'all current integration original artifacts accounted')
log_archive_path=ROOT/'official-run-logs'/f'integration-{integration["id"]}.zip'
log_receipts=[]
with zipfile.ZipFile(log_archive_path)as archive:
    for job in jobs:
        members=[name for name in archive.namelist()if re.fullmatch(r'\d+_'+re.escape(job['name'].replace('/','_'))+r'\.txt',name)]
        require(len(members)==1,job['name']+' unique original whole-job member')
        direct=ROOT/'job-logs'/(str(job['id'])+'.txt')
        require(archive.read(members[0])==direct.read_bytes(),job['name']+' original run ZIP and endpoint log equality')
        log_receipts.append(dict(id=job['id'],name=job['name'],sha256=hashlib.sha256(direct.read_bytes()).hexdigest()))

canvas=next(row for row in browser if row['name']=='browser (canvas)')
canvas_path=ROOT/'job-logs'/(str(canvas['id'])+'.txt')
canvas_lines=canvas_path.read_text().splitlines()
result_at=next(index for index,line in enumerate(canvas_lines)if 'Z CDP_RESULT {'in line)
diagnostics=[dict(line=index+1,text=line)for index,line in enumerate(canvas_lines)
             if 'Exception occurred during processing of request'in line or 'BrokenPipeError:'in line]
require(all(row['line']>result_at+1 for row in diagnostics),'server request diagnostics follow browser result in appended server log')
canvas['server_log_diagnostics']=dict(lines=diagnostics,classification='Appended server request diagnostics are retained separately from uncaught browser exceptions and controlled assertions; exact socket-closure cause is not inferred.')
report=dict(review_passed=True,overall_ci_accepted=False,native_accepted=False,browser_accepted=True,
            mutation_official_api_conclusion='success',mutation_artifact_acceptance_outside_this_review=True,
            check_count=checks,pr_head=HEAD,execution_commit=MERGE,execution_tree=tree,merge_parents=parents,
            integration_run_id=41388718270,integration_conclusion='failure',mutation_run_id=41388718083,
            current_registry_suite_count=len(registry),native_partitions=[len(plan)for plan in planned],native=native,
            counted_tests=sum(row['total']for row in native),counted_passed=sum(row['passed']for row in native),
            allowed_skips=sum(row['allowed_skips']for row in native),native_bad_rows=bad_rows,native_job_logs=native_jobs,
            python_receipts_checked=python_count,node_logs_checked=node_count,browser=browser,
            full_stale_bridge_ids=sorted(stale_ids,key=lambda rid:int(rid[1:])),stale_bridge_count=len(stale_ids),
            freshness_raw_log_sha256=hashlib.sha256(raw_freshness_path.read_bytes()).hexdigest(),
            official_negative_control=proof,official_native_complete_summary_present=False,
            integration_official_zip_count=len(zip_rows),integration_official_zips=zip_rows,
            integration_whole_job_logs_byte_equal=log_receipts,current_expected_sha256=expected_digest,current_timings_sha256=timings_digest,
            audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=inputs,
            scope='Only saved API/artifact/raw log/source and Git metadata read. Current registry/expected/timing derived at this HEAD. No network, product, Chrome, build, source/PR writes, or local negative control/test executions.')
(OUT/'native-browser-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:report[key]for key in ['review_passed','overall_ci_accepted','native_accepted','browser_accepted','check_count','current_registry_suite_count','native_partitions','counted_tests','counted_passed','allowed_skips','python_receipts_checked','node_logs_checked','stale_bridge_count']},ensure_ascii=False))
